pipeline {
  agent any

  environment {
    // SONAR_HOST_URL and SONAR_TOKEN should be configured in Jenkins global config or as credentials
    // Example: Manage Jenkins > Configure System > SonarQube servers
    // SONARQUBE_ENV = 'SonarQubeServerName'
  }

  options {
    timestamps()
    ansiColor('xterm')
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
      environment {
        // Ensure you have configured SonarQube server in Jenkins and name matches below
        // SONARQUBE_ENV = 'SonarQubeServerName'
      }
      steps {
        withSonarQubeEnv('SonarQubeServerName') {
          sh '. venv/bin/activate && sonar-scanner -Dsonar.projectKey=aceest-fitness'
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
    failure {
      echo 'Pipeline failed.'
    }
  }
}
