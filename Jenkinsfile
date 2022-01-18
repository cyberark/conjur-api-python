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
          cobertura(
            coberturaReportFile: "coverage.xml",
            onlyStable: false,
            failNoReports: true,
            failUnhealthy: false,
            failUnstable: false,
            autoUpdateHealth: true,
            autoUpdateStability: true,
            zoomCoverageChart: true,
            maxNumberOfBuilds: 0,
            lineCoverageTargets: '80, 80, 80',
            conditionalCoverageTargets: '80, 80, 80',
            classCoverageTargets: '80, 80, 80',
            fileCoverageTargets: '80, 80, 80',
        )
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
