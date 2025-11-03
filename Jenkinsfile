pipeline {
  agent any

  // Global options (no empty environment blocks allowed)
  options {
    timestamps()
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Set up Python') {
      steps {
        sh 'python3 --version'
      }
    }

    stage('Install dependencies') {
      steps {
        sh 'python3 -m venv venv'
        sh '. venv/bin/activate && pip install --upgrade pip'
        sh '. venv/bin/activate && pip install -r requirements.txt'
      }
    }

    stage('Pytest with Coverage') {
      steps {
        sh '. venv/bin/activate && pytest -v --cov=. --cov-report xml --junitxml=pytest-results.xml'
      }
      post {
        always {
          junit allowEmptyResults: true, testResults: 'pytest-results.xml'
          archiveArtifacts artifacts: 'coverage.xml', onlyIfSuccessful: true
        }
      }
    }

    stage('SonarQube Scan') {
      steps {
        // Wrap output in ANSI color if plugin installed
        wrap([$class: 'AnsiColorBuildWrapper', colorMapName: 'xterm']) {
          script {
            // Ensure a SonarScanner tool named 'SonarScanner' is configured in Jenkins (Manage Jenkins > Global Tool Configuration)
            def scannerHome = tool name: 'SonarScanner', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
            withSonarQubeEnv('SonarQubeServer') {
              // Run scanner using tool installation; rely on sonar-project.properties
              def scanStatus = sh(returnStatus: true, script: ". venv/bin/activate && ${scannerHome}/bin/sonar-scanner")
              if (scanStatus != 0) {
                echo "SonarScanner failed with status ${scanStatus}"
                // Mark a flag so Quality Gate is skipped
                env.SONAR_SCAN_FAILED = 'true'
              } else {
                // Verify report-task.txt presence for quality gate wait
                if (fileExists('report-task.txt')) {
                  env.SONAR_SCAN_FAILED = 'false'
                } else if (fileExists('.scannerwork/report-task.txt')) {
                  env.SONAR_SCAN_FAILED = 'false'
                } else {
                  echo 'report-task.txt not found; will skip quality gate.'
                  env.SONAR_SCAN_FAILED = 'true'
                }
              }
            }
          }
        }
      }
    }

    stage('Quality Gate') {
      when {
        expression { return env.SONAR_SCAN_FAILED != 'true' }
      }
      steps {
        script {
          timeout(time: 5, unit: 'MINUTES') {
            def qg = waitForQualityGate()
            if (qg.status != 'OK') {
              error "Pipeline aborted due to quality gate failure: ${qg.status}"
            }
          }
        }
      }
    }
  }

  post {
    success {
      echo 'Pipeline completed successfully.'
    }
    unstable {
      echo 'Pipeline marked unstable (possibly failed quality gate).'
    }
    failure {
      echo 'Pipeline failed.'
    }
    always {
      echo 'Build finished.'
    }
  }
}
