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

  triggers {
    cron(getDailyCronString())
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
        }
      }
    }

    stage('Validate') {
      parallel {
        stage('Changelog') {
          steps {
            script { infrapool.agentSh './ci/test/parse-changelog.sh' }
          }
        }
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
            cobertura(
              coberturaReportFile: "coverage.xml",
              onlyStable: false,
              failNoReports: true,
              failUnhealthy: true,
              failUnstable: false,
              autoUpdateHealth: false,
              autoUpdateStability: false,
              zoomCoverageChart: true,
              maxNumberOfBuilds: 0,
              lineCoverageTargets: '40, 40, 40',
              conditionalCoverageTargets: '80, 80, 80',
              classCoverageTargets: '80, 80, 80',
              fileCoverageTargets: '80, 80, 80',
            )
            codacy action: 'reportCoverage', filePath: "coverage.xml"
          }
        }
      }
    }

    stage('Integration tests') {
      steps {
        script {
          grantIPAccess(infrapool)
          infrapool.agentSh './ci/test/test_integration --environment ubuntu'
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
    }
  }
}
