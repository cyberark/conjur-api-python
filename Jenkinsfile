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
    stage('Unit tests') {
      steps {
        sh './ci/testing/test_unit.sh'
      }
    }

    // Only publish if the HEAD is tagged with the same version as in __version__.py
    stage('Publish') {
      parallel {
        stage('Publish to PyPI') {
          steps {
            sh 'summon -e testing ./bin/publish_package'
          }
//          when {
//            tag "v*"
//          }
        }
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
