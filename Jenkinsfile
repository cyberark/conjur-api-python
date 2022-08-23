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
    stage('Double check something') {
      steps {
        sh '''
          git remote -v
          if [[ $(git remote -v) =~ github.com[:/]([^/]*/[^ .]*) ]]; then
            echo "${BASH_REMATCH[1]}"
          else
            echo "No match"
          fi'''
      }
    }
  }
  post {
    always {
      cleanupAndNotify(currentBuild.currentResult)
    }
  }
}
