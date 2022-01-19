#!/usr/bin/env groovy

pipeline {
  agent { label 'executor-v2' }

  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '30'))
  }

  triggers {
    cron(getDailyCronString())
  }
  stages {
      stage('Linting') {
        steps { sh './ci/testing/test_linting.sh' }
      }

    stage('Unit tests') {
     steps {
       sh './ci/testing/test_unit.sh'
     }
    }

    stage('Publish to PyPI') {
      steps {
        echo 'Check if publish is required'
        sh 'summon -e production ./ci/publish/run_is_publish_required'

        sh 'summon -e production ./ci/publish/publish_package'
      steps {
        sh './ci/test/test_unit.sh'
      }
      post {
        always {
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
        }
      }
    }

    stage('Integration tests') {
      steps {
        sh './ci/test/test_integration --environment ubuntu'
      }

      post {
        always {
          junit 'ci/test/output/**/*.xml'
        }
      }
      when {
        tag "v*"
      }
    }
  }
  post {
    always {
      cleanupAndNotify(currentBuild.currentResult)
    }
    unsuccessful {
      script {
          cleanupAndNotify(currentBuild.currentResult, notify_team_teams = 'Secrets Manager HQ')
      }
    }
  }
}
