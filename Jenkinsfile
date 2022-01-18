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
      post {
        always {
          junit 'ci/testing/output/**/*.xml'
          ccCoverage("coverage.py")
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
