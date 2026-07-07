// Command mock-oidc-server wraps github.com/oauth2-proxy/mockoidc as a
// standalone HTTP server for use in Conjur's Python SDK integration tests.
//
// mockoidc's authorization_endpoint issues a redirect with a code
// immediately (no login form), which is what makes it usable headlessly
// from a test suite that has no browser.
//
// The server generates its own self-signed TLS certificate at startup and
// serves HTTPS only, so integration tests exercise real TLS/cert-trust
// handling against an OIDC provider. The certificate is written to disk
// (CERT_PATH) so the test harness can install it into Conjur's trust store.
//
// Two extra endpoints not provided by mockoidc itself:
//
//	GET  /mock/config      returns {"client_id", "client_secret"}
//	POST /mock/queue-user  body {"subject": "..."} queues the identity that
//	                        the next call to the authorization_endpoint will
//	                        log in as
package main

import (
	"bytes"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/json"
	"encoding/pem"
	"io"
	"log"
	"math/big"
	"net"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strconv"
	"time"

	"github.com/oauth2-proxy/mockoidc"
)

func main() {
	listenAddr := os.Getenv("LISTEN_ADDR")
	if listenAddr == "" {
		listenAddr = ":443"
	}
	// The hostname:port other containers use to reach this server, e.g.
	// "mock-oidc-server:443". mockoidc derives every URL in its discovery
	// document (issuer, authorization_endpoint, token_endpoint, ...) from
	// this value, so it must be externally resolvable, not the local bind
	// address.
	publicAddr := os.Getenv("PUBLIC_ADDR")
	if publicAddr == "" {
		log.Fatal("PUBLIC_ADDR must be set to the externally-reachable host:port")
	}

	certPath := os.Getenv("CERT_PATH")
	if certPath == "" {
		certPath = "/certs/oidc-server.cert.pem"
	}

	tlsConfig, err := generateTLSConfig(publicAddr, certPath)
	if err != nil {
		log.Fatalf("failed to generate TLS certificate: %v", err)
	}

	m, err := mockoidc.NewServer(nil)
	if err != nil {
		log.Fatalf("failed to create mock OIDC server: %v", err)
	}

	if clientID := os.Getenv("CLIENT_ID"); clientID != "" {
		m.ClientID = clientID
	}
	if clientSecret := os.Getenv("CLIENT_SECRET"); clientSecret != "" {
		m.ClientSecret = clientSecret
	}

	// mockoidc.Issuer()/Addr() decide the "https://" vs "http://" scheme
	// used in the discovery document and ID token `iss` claims by reading
	// a private field that is only ever set inside Start(). Trip that flag
	// with a throwaway listener, then discard the server Start created:
	// we take over serving ourselves below with our own mux (which adds
	// /mock/config, /mock/queue-user, and the client_secret_basic
	// middleware that Start()'s internal mux doesn't have).
	dummyLn, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatalf("failed to create throwaway listener: %v", err)
	}
	if err := m.Start(dummyLn, tlsConfig); err != nil {
		log.Fatalf("failed to prime TLS state: %v", err)
	}
	if err := m.Shutdown(); err != nil {
		log.Fatalf("failed to stop throwaway TLS server: %v", err)
	}

	mux := http.NewServeMux()
	mux.HandleFunc(mockoidc.AuthorizationEndpoint, m.Authorize)
	mux.HandleFunc(mockoidc.TokenEndpoint, basicAuthToFormMiddleware(m.Token))
	mux.HandleFunc(mockoidc.UserinfoEndpoint, m.Userinfo)
	mux.HandleFunc(mockoidc.JWKSEndpoint, m.JWKS)
	mux.HandleFunc(mockoidc.DiscoveryEndpoint, m.Discovery)
	mux.HandleFunc("/mock/config", configHandler(m))
	mux.HandleFunc("/mock/queue-user", queueUserHandler(m))

	m.Server = &http.Server{
		Addr:      publicAddr,
		Handler:   mux,
		TLSConfig: tlsConfig,
	}

	ln, err := net.Listen("tcp", listenAddr)
	if err != nil {
		log.Fatalf("failed to listen on %s: %v", listenAddr, err)
	}

	log.Printf("mock-oidc-server listening on %s, public address %s", listenAddr, publicAddr)
	if err := m.Server.ServeTLS(ln, "", ""); err != nil && err != http.ErrServerClosed {
		log.Fatalf("server error: %v", err)
	}
}

// generateTLSConfig creates a self-signed certificate for host (its
// hostname, port stripped) and writes the PEM-encoded cert to certPath so
// it can be installed into a peer's trust store.
func generateTLSConfig(host, certPath string) (*tls.Config, error) {
	hostname := host
	if h, _, err := net.SplitHostPort(host); err == nil {
		hostname = h
	}

	priv, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		return nil, err
	}

	serialNumber, err := rand.Int(rand.Reader, new(big.Int).Lsh(big.NewInt(1), 128))
	if err != nil {
		return nil, err
	}

	template := x509.Certificate{
		SerialNumber:          serialNumber,
		Subject:               pkix.Name{CommonName: hostname},
		NotBefore:             time.Now().Add(-time.Hour),
		NotAfter:              time.Now().Add(24 * time.Hour),
		KeyUsage:              x509.KeyUsageDigitalSignature | x509.KeyUsageCertSign,
		ExtKeyUsage:           []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
		BasicConstraintsValid: true,
		IsCA:                  true,
		DNSNames:              []string{hostname},
	}

	derBytes, err := x509.CreateCertificate(rand.Reader, &template, &template, &priv.PublicKey, priv)
	if err != nil {
		return nil, err
	}
	certPEM := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: derBytes})

	keyDER, err := x509.MarshalECPrivateKey(priv)
	if err != nil {
		return nil, err
	}
	keyPEM := pem.EncodeToMemory(&pem.Block{Type: "EC PRIVATE KEY", Bytes: keyDER})

	cert, err := tls.X509KeyPair(certPEM, keyPEM)
	if err != nil {
		return nil, err
	}

	if err := os.MkdirAll(filepath.Dir(certPath), 0755); err != nil {
		return nil, err
	}
	if err := os.WriteFile(certPath, certPEM, 0644); err != nil {
		return nil, err
	}

	return &tls.Config{Certificates: []tls.Certificate{cert}}, nil
}

// basicAuthToFormMiddleware copies client_id/client_secret from an HTTP Basic
// Auth header (the "client_secret_basic" token endpoint auth method, which
// the discovery document advertises as supported) into the request's form
// body, since mockoidc's Token handler only ever reads those two params from
// the form and never looks at the Authorization header.
func basicAuthToFormMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(rw http.ResponseWriter, req *http.Request) {
		clientID, clientSecret, ok := req.BasicAuth()
		if !ok {
			next(rw, req)
			return
		}

		body, err := io.ReadAll(req.Body)
		if err != nil {
			http.Error(rw, err.Error(), http.StatusBadRequest)
			return
		}

		form, err := url.ParseQuery(string(body))
		if err != nil {
			http.Error(rw, err.Error(), http.StatusBadRequest)
			return
		}
		form.Set("client_id", clientID)
		form.Set("client_secret", clientSecret)

		encoded := form.Encode()
		req.Body = io.NopCloser(bytes.NewReader([]byte(encoded)))
		req.ContentLength = int64(len(encoded))
		req.Header.Set("Content-Length", strconv.Itoa(len(encoded)))
		req.Form = nil
		req.PostForm = nil

		next(rw, req)
	}
}

func configHandler(m *mockoidc.MockOIDC) http.HandlerFunc {
	return func(rw http.ResponseWriter, req *http.Request) {
		rw.Header().Set("Content-Type", "application/json")
		json.NewEncoder(rw).Encode(map[string]string{
			"client_id":     m.ClientID,
			"client_secret": m.ClientSecret,
		})
	}
}

type queueUserRequest struct {
	Subject string `json:"subject"`
}

func queueUserHandler(m *mockoidc.MockOIDC) http.HandlerFunc {
	return func(rw http.ResponseWriter, req *http.Request) {
		if req.Method != http.MethodPost {
			http.Error(rw, "method not allowed", http.StatusMethodNotAllowed)
			return
		}

		var body queueUserRequest
		if err := json.NewDecoder(req.Body).Decode(&body); err != nil {
			http.Error(rw, err.Error(), http.StatusBadRequest)
			return
		}
		if body.Subject == "" {
			http.Error(rw, "subject is required", http.StatusBadRequest)
			return
		}

		m.QueueUser(&mockoidc.MockUser{Subject: body.Subject})
		rw.WriteHeader(http.StatusNoContent)
	}
}
