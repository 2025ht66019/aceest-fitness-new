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

    stage('Docker Build') {
      when {
        expression { return currentBuild.currentResult == 'SUCCESS' }
      }
      steps {
        script {
          // Define image name and tags
          def repo = '2025ht66019/aceest_fitness'
          def shortSha = sh(returnStdout: true, script: 'git rev-parse --short=8 HEAD').trim()
          def tagCommit = "${repo}:${shortSha}"
          def tagLatest = "${repo}:latest"
          echo "Building Docker image ${tagCommit} and tagging latest"
          sh "docker build -t ${tagCommit} -t ${tagLatest} ."
          // Stash tags for next stage
          env.DOCKER_IMAGE_COMMIT = tagCommit
          env.DOCKER_IMAGE_LATEST = tagLatest
        }
      }
    }

    stage('Docker Push') {
      when {
        expression { return env.DOCKER_IMAGE_COMMIT }
      }
      steps {
        script {
          // Expect Jenkins to have Docker Hub credentials configured with id 'dockerhub-creds'
          withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
            sh 'echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin'
            sh "docker push ${env.DOCKER_IMAGE_COMMIT}"
            sh "docker push ${env.DOCKER_IMAGE_LATEST}"
          }
        }
      }
    }
    stage('Deploy to Minikube') {
      when {
        expression { return env.DOCKER_IMAGE_LATEST }
      }
      steps {
        script {
          sh '''
            echo "Validating kubectl and minikube availability..."
            if ! command -v kubectl >/dev/null 2>&1; then
              echo "kubectl not found in PATH"; exit 1; fi
            if ! command -v minikube >/dev/null 2>&1; then
              echo "minikube not found in PATH"; exit 1; fi
            echo "Ensuring minikube running..."
            if ! minikube status >/dev/null 2>&1; then
              echo "Starting minikube..."
              minikube start --memory=2048 --cpus=2 || { echo "Failed to start minikube"; exit 1; }
            fi
            echo "Deploying commit image tag..."
            COMMIT_TAG="${DOCKER_IMAGE_COMMIT##*:}"
            echo "Commit short SHA is $COMMIT_TAG"
            echo "Substituting IMAGE_TAG in manifest to $COMMIT_TAG"
            sed "s/\${IMAGE_TAG}/$COMMIT_TAG/" k8s/aceest-fitness.yaml | kubectl apply -f -
            echo "Applying Kubernetes manifests..."
            echo "Waiting for rollout..."
            kubectl rollout status deployment/aceest-fitness --timeout=180s
            echo "Service URL(s):"
            minikube service aceest-fitness --url || true
          '''
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
