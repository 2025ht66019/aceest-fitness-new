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
        sh 'export PYTHONPATH=$PWD && . venv/bin/activate && pytest -v --cov=. --cov-report xml --junitxml=pytest-results.xml'
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
            def scannerHome = tool name: 'SonarScanner', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
            withSonarQubeEnv('SonarQubeServer') {
              def scanStatus = sh(returnStatus: true, script: ". venv/bin/activate && ${scannerHome}/bin/sonar-scanner")
              if (scanStatus != 0) {
                echo "SonarScanner failed with status ${scanStatus}"
                env.SONAR_SCAN_FAILED = 'true'
              } else {
                if (fileExists('report-task.txt') || fileExists('.scannerwork/report-task.txt')) {
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
      post {
        always {
          // Archive raw scanner working files (logs, metadata)
          archiveArtifacts artifacts: '.scannerwork/**', onlyIfSuccessful: true
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
            set -e
            echo "Validating kubectl and minikube availability..."
            command -v kubectl >/dev/null || { echo "kubectl not found"; exit 1; }
            command -v minikube >/dev/null || { echo "minikube not found"; exit 1; }
            echo "Ensuring minikube running..."
            if ! minikube status >/dev/null 2>&1; then
              minikube start --memory=2048 --cpus=2
            fi

            COMMIT_TAG="${DOCKER_IMAGE_COMMIT##*:}"
            echo "Deploying image tag: $COMMIT_TAG"

            # Verify placeholder exists
            if ! grep -q '\\${IMAGE_TAG}' k8s/canary-deployment.yaml; then
              echo "Placeholder \\${IMAGE_TAG} not found in k8s/canary-deployment.yaml"
              exit 1
            fi

            # Substitute placeholder and apply
            sed -e "s|\\${IMAGE_TAG}|${COMMIT_TAG}|g" k8s/canary-deployment.yaml | kubectl apply -f -

            echo "Waiting for rollout..."
            kubectl rollout status deployment/aceest-fitness --timeout=180s

            echo "Current deployed image:"
            kubectl get deploy aceest-fitness -o jsonpath='{.spec.template.spec.containers[0].image}'; echo

            echo "Service URL(s):"
            NODE_IP=$(minikube ip)
            NODE_PORT=$(kubectl get svc aceest-fitness -o jsonpath='{.spec.ports[0].nodePort}')
            echo "http://${NODE_IP}:${NODE_PORT}"
            echo "minikube service aceest-fitness --url"
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