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
          withSonarQubeEnv('SonarQubeServer') {
            // Use configuration from sonar-project.properties; pass coverage already generated
            sh '. venv/bin/activate && sonar-scanner'
          }
        }
      }
    }

    stage('Quality Gate') {
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
