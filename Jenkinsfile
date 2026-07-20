#!/usr/bin/env groovy
@Library("product-pipelines-shared-library") _

// Automated release, promotion and dependencies
properties([
  // Include the automated release parameters for the build
  release.addParams(),
  // Dependencies of the project that should trigger builds
  // dependencies([ ])
])

// Performs release promotion.  No other stages will be run
if (params.MODE == "PROMOTE") {
  release.promote(params.VERSION_TO_PROMOTE) { infrapool, sourceVersion, targetVersion, assetDirectory ->
    // Any assets from sourceVersion Github release are available in assetDirectory
    // Any version number updates from sourceVersion to targetVersion occur here
    // Any publishing of targetVersion artifacts occur here
    // Anything added to assetDirectory will be attached to the Github Release

    // Publish target version.
    infrapool.agentSh "summon -e production ./ci/publish/publish_package ${targetVersion}"
  }

  // Copy Github Enterprise release to Github
  release.copyEnterpriseRelease(params.VERSION_TO_PROMOTE)
  return
}

pipeline {
  agent { label 'conjur-enterprise-common-agent' }

  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '30'))
  }

  environment {
    // Sets the MODE to the specified or autocalculated value as appropriate
    MODE = release.canonicalizeMode()
  }

  parameters {
    booleanParam(name: 'TEST_CLOUD', defaultValue: false, description: 'Run integration tests against a Conjur Cloud tenant')
    booleanParam(name: 'RUN_AZURE_TESTS', defaultValue: false, description: 'Run Azure managed identity integration tests on an AzureExecutorV2 agent')
    booleanParam(name: 'RUN_AWS_TESTS', defaultValue: false, description: 'Run AWS IAM integration tests on an ExecutorV2 agent')
    booleanParam(name: 'RUN_GCP_TESTS', defaultValue: false, description: 'Run GCP integration tests on a GcpExecutorV2 agent')
  }

  triggers {
    parameterizedCron("""
      ${getDailyCronString("%TEST_CLOUD=true")}
      ${getWeeklyCronString("H(1-5)", "%MODE=RELEASE")}
    """)
  }

  stages {
    // Aborts any builds triggered by another project that wouldn't include any changes
    stage ("Skip build if triggering job didn't create a release") {
      when {
        expression {
          MODE == "SKIP"
        }
      }
      steps {
        script {
          currentBuild.result = 'ABORTED'
          error("Aborting build because this build was triggered from upstream, but no release was built")
        }
      }
    }

    stage('Scan for internal URLs') {
      steps {
        script {
          detectInternalUrls()
        }
      }
    }

    stage('Get InfraPool ExecutorV2 Agent') {
      steps {
        script {
          // Request ExecutorV2 agents for 1 hour(s)
          infrapool = getInfraPoolAgent.connected(type: "ExecutorV2", quantity: 1, duration: 1)[0]

          if (params.RUN_AZURE_TESTS) {
            INFRAPOOL_AZURE_EXECUTORV2_AGENTS = getInfraPoolAgent(type: "AzureExecutorV2", quantity: 1, duration: 1)
            INFRAPOOL_AZURE_EXECUTORV2_AGENT_0 = INFRAPOOL_AZURE_EXECUTORV2_AGENTS[0]
            azureInfrapool = infraPoolConnect(INFRAPOOL_AZURE_EXECUTORV2_AGENT_0, {})
          }

          if (params.RUN_GCP_TESTS) {
            INFRAPOOL_GCP_EXECUTORV2_AGENTS = getInfraPoolAgent(type: "GcpExecutorV2", quantity: 1, duration: 1)
            INFRAPOOL_GCP_EXECUTORV2_AGENT_0 = INFRAPOOL_GCP_EXECUTORV2_AGENTS[0]
            gcpInfrapool = infraPoolConnect(INFRAPOOL_GCP_EXECUTORV2_AGENT_0, {})
          }
        }
      }
    }

    stage('Validate') {
      parallel {
        stage('Linting') {
          steps {
            script { infrapool.agentSh './ci/test/test_linting.sh' }
          }
        }
      }
    }

    // Generates a VERSION file based on the current build number and latest version in CHANGELOG.md
    stage('Validate changelog and set version') {
      steps {
        script {
          updateVersion(infrapool, "CHANGELOG.md", "${BUILD_NUMBER}")
        }
      }
    }

    stage('Unit tests') {
      steps {
        script {
          infrapool.agentSh './ci/test/test_unit.sh'
        }
      }
      post {
        always {
          script {
            infrapool.agentStash name: 'xml-unit-tests', includes: 'ci/test/output/*.xml'
            infrapool.agentStash name: 'coverage', includes: 'coverage.*'
            unstash 'xml-unit-tests'
            unstash 'coverage'
            sh 'find . -iname "*.xml" || true'
            junit 'ci/test/output/**/*.xml'
            recordCoverage(
              tools: [[parser: 'COBERTURA', pattern: 'coverage.xml']],
              sourceCodeEncoding: 'ASCII',
              qualityGates: [
                  [threshold: 40.0, metric: 'LINE', baseline: 'PROJECT', unstable: true],
                  [threshold: 80.0, metric: 'BRANCH', baseline: 'PROJECT', unstable: true],
                  [threshold: 80.0, metric: 'METHOD', baseline: 'PROJECT', unstable: true]
              ],
              skipPublishingChecks: false
            )
            codacy action: 'reportCoverage', filePath: "coverage.xml"
          }
        }
      }
    }

    stage('Integration tests') {
      environment {
        INFRAPOOL_REGISTRY_URL = "registry.tld"
      }
      steps {
        script {
          grantIPAccess(infrapool)
          infrapool.agentSh './ci/test/test_integration'
        }
      }

      post {
        always {
          script {
            infrapool.agentStash name: 'xml-integration-tests', includes: 'ci/test/output/*.xml'
            unstash 'xml-integration-tests'
            junit 'ci/test/output/**/*.xml'
          }
        }
      }
    }

    stage('Run Azure tests') {
      when {
        expression { params.RUN_AZURE_TESTS }
      }
      steps {
        script {
          azureInfrapool.agentSh '''
            set +e
            export RUN_AZURE_TESTS=true
            export PYTEST_JUNIT_OUTPUT=ci/test/output/pytest-integration-junit-azure.xml
            summon -e azure ./ci/test/test_integration
            rc=$?
            exit $rc
          '''
        }
      }
      post {
        always {
          script {
            azureInfrapool.agentStash name: 'xml-azure-tests', includes: 'ci/test/output/pytest-integration-junit-azure.xml'
            unstash 'xml-azure-tests'
            junit 'ci/test/output/pytest-integration-junit-azure.xml'
          }
        }
      }
    }

    stage('Run AWS tests') {
      when {
        expression { params.RUN_AWS_TESTS }
      }
      steps {
        script {
          def awsInfrapool = getInfraPoolAgent.connected(type: "ExecutorV2", quantity: 1, duration: 1)[0]
          def callerIdentityJson = awsInfrapool.agentSh(script: 'aws sts get-caller-identity', returnStdout: true).trim()
          def awsAccountId = (callerIdentityJson =~ /"Account"\s*:\s*"([^"]+)"/)[0][1]
          def awsArn       = (callerIdentityJson =~ /"Arn"\s*:\s*"([^"]+)"/)[0][1]
          def awsRoleName  = awsArn.tokenize('/')[1]

          awsInfrapool.agentSh """
            set +e
            export RUN_AWS_TESTS=true
            export AWS_ACCOUNT_ID="${awsAccountId}"
            export AWS_ROLE_NAME="${awsRoleName}"
            export PYTEST_JUNIT_OUTPUT=ci/test/output/pytest-integration-junit-aws.xml
            ./ci/test/test_integration
            rc=\$?
            exit \$rc
          """
          awsInfrapool.agentStash name: 'xml-aws-tests', includes: 'ci/test/output/pytest-integration-junit-aws.xml'
        }
      }
      post {
        always {
          script {
            unstash 'xml-aws-tests'
            junit 'ci/test/output/pytest-integration-junit-aws.xml'
          }
        }
      }
    }

    stage('Run GCP tests') {
      when {
        expression { params.RUN_GCP_TESTS }
      }
      steps {
        script {
          // Fetch token on the GCP agent (has metadata server access), stash the
          // output files, then transfer them to infrapool (which has Docker) so the
          // token value is never interpolated into a Groovy string or visible in logs.
          gcpInfrapool.agentSh './ci/get_gcp_token.sh "data/test/gcp-apps/test-app" "conjur" gcp-ctx'
          gcpInfrapool.agentStash name: 'gcp-ctx', includes: 'gcp-ctx/**'
          infrapool.agentUnstash name: 'gcp-ctx'

          infrapool.agentSh '''
            set +e
            export RUN_GCP_TESTS=true
            export GCP_ID_TOKEN="$(cat gcp-ctx/token)"
            export GCP_PROJECT_ID="$(cat gcp-ctx/project-id)"
            export PYTEST_JUNIT_OUTPUT=ci/test/output/pytest-integration-junit-gcp.xml
            ./ci/test/test_integration
            rc=$?
            rm -rf gcp-ctx
            exit $rc
          '''
          infrapool.agentStash name: 'xml-gcp-tests', includes: 'ci/test/output/pytest-integration-junit-gcp.xml'
        }
      }
      post {
        always {
          script {
            unstash 'xml-gcp-tests'
            junit 'ci/test/output/pytest-integration-junit-gcp.xml'
          }
        }
      }
    }

    stage('Run Conjur Cloud tests') {
      when {
        expression { params.TEST_CLOUD }
      }
      stages {
        stage('Create a Tenant') {
          steps {
            script {
              TENANT = getConjurCloudTenant()
            }
          }
        }
        stage('Authenticate') {
          steps {
            script {
              def id_token = getConjurCloudTenant.tokens(
                infrapool: infrapool,
                identity_url: "${TENANT.identity_information.idaptive_tenant_fqdn}",
                username: "${TENANT.login_name}"
              )

              def conj_token = getConjurCloudTenant.tokens(
                infrapool: infrapool,
                conjur_url: "${TENANT.conjur_cloud_url}",
                identity_token: "${id_token}"
                )

              env.identity_token = id_token
              env.conj_token = conj_token
            }
          }
        }
        stage('Run tests against Tenant') {
          environment {
            INFRAPOOL_REGISTRY_URL = "registry.tld"
            INFRAPOOL_CONJUR_APPLIANCE_URL="${TENANT.conjur_cloud_url}"
            INFRAPOOL_CONJUR_AUTHN_LOGIN="${TENANT.login_name}"
            INFRAPOOL_CONJUR_AUTHN_TOKEN="${env.conj_token}"
            INFRAPOOL_IDENTITY_TOKEN="${env.identity_token}"
            INFRAPOOL_TEST_CLOUD=true
          }
          steps {
            script {
              grantIPAccess(infrapool)
              infrapool.agentSh './ci/test/test_integration'
            }
          }
        }
      }
      post {
        always {
          script {
            infrapool.agentStash name: 'cloud-integration-tests', includes: 'ci/test/output/*.xml'
            unstash 'cloud-integration-tests'
            junit 'ci/test/output/**/*.xml'
            deleteConjurCloudTenant("${TENANT.id}")
          }
        }
      }
    }

    stage('Release') {
      when {
        expression {
          MODE == "RELEASE"
        }
      }

      steps {
        release(infrapool) { billOfMaterialsDirectory, assetDirectory, toolsDirectory ->
          // Publish release artifacts to all the appropriate locations
          // Copy any artifacts to assetDirectory to attach them to the Github release
        }
      }
    }
  }

  post {
    always {
      removeIPAccess(infrapool)
      releaseInfraPoolAgent(".infrapool/release_agents")

      script {
        // Resolve ownership issue before running infra post hook
        sh 'git config --global --add safe.directory ${PWD}'

        // TODO: Remove try-catch once the Slack plugin is fixed on the Jenkins
        // controller. The Slack plugin currently crashes with:
        //   java.lang.ClassNotFoundException: net.sf.json.groovy.JsonSlurper
        // because it depends on json-lib which is no longer on the classpath
        // after a recent plugin upgrade. Wrapping here prevents the Slack
        // plugin bug from masking real build failures.
        // See: CNJR-13102
        try {
          infraPostHook()
        } catch (Throwable err) {
          echo "WARNING: infraPostHook() failed — likely a Slack plugin issue: ${err}"
        }
      }
    }
  }
}
