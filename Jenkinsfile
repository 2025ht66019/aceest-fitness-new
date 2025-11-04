pipeline {
  agent any
  
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
        // Prefer the Python launcher on Windows
        powershell 'py -3 --version; python --version'
      }
    }

    stage('Install dependencies') {
      steps {
        powershell '''
          $ErrorActionPreference = 'Stop'
          py -3 -m venv venv
          .\\venv\\Scripts\\Activate.ps1
          $env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
          python -m pip install --upgrade pip
          if (Test-Path requirements.txt) {
            pip install -r requirements.txt
          } else {
            Write-Host "requirements.txt not found; skipping."
          }
        '''
      }
    }

    stage('Pytest with Coverage') {
      steps {
        powershell '''
          $ErrorActionPreference = 'Stop'
          .\\venv\\Scripts\\Activate.ps1
          # write coverage.xml explicitly so the artifact step can find it
          python -m pytest -v --cov=. --cov-report "xml:coverage.xml" --junitxml=pytest-results.xml
        '''
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
        wrap([$class: 'AnsiColorBuildWrapper', colorMapName: 'xterm']) {
          script {
            def scannerHome = tool name: 'SonarScanner', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
            withSonarQubeEnv('SonarQubeServer') {
              // Use the Windows .bat entrypoint
              def status = powershell(
                returnStatus: true,
                script: """
                  \$ErrorActionPreference = 'Stop'
                  .\\venv\\Scripts\\Activate.ps1
                  & "${scannerHome}\\bin\\sonar-scanner.bat"
                  exit \$LASTEXITCODE
                """
              )
              if (status != 0) {
                echo "SonarScanner failed with status ${status}"
                env.SONAR_SCAN_FAILED = 'true'
              } else {
                // Check both possible locations for report-task.txt on Windows
                def hasReport = fileExists('report-task.txt') || fileExists('.scannerwork/report-task.txt')
                if (!hasReport) {
                  echo 'report-task.txt not found; will skip quality gate.'
                  env.SONAR_SCAN_FAILED = 'true'
                } else {
                  env.SONAR_SCAN_FAILED = 'false'
                }
              }
            }
          }
        }
      }
    }

    stage('Quality Gate') {
      when { expression { return env.SONAR_SCAN_FAILED != 'true' } }
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
      when { expression { return currentBuild.currentResult == 'SUCCESS' } }
      steps {
        script {
          powershell '''
          $ErrorActionPreference = 'Stop'
          $repo = '2025ht66019/aceest_fitness'
          $shortSha = (git rev-parse --short=8 HEAD).Trim()

          # Avoid $repo:... parsing; use concatenation
          $tagCommit = $repo + ":" + $shortSha
          $tagLatest = $repo + ":latest"

          Write-Host "Building Docker image $tagCommit and tagging latest"
          docker build -t $tagCommit -t $tagLatest .

          # Export for later stages
          "DOCKER_IMAGE_COMMIT=$tagCommit" | Out-File -FilePath $env:WORKSPACE\\docker_vars.env -Encoding ascii
          "DOCKER_IMAGE_LATEST=$tagLatest" | Out-File -FilePath $env:WORKSPACE\\docker_vars.env -Append -Encoding ascii
        '''
        // Read values and set env.* without dynamic putAt
        def lines = readFile('docker_vars.env').readLines()
        for (def l : lines) {
          if (!l?.trim()) continue
          def parts = l.trim().split('=', 2)
          if (parts.size() != 2) continue
          if (parts[0] == 'DOCKER_IMAGE_COMMIT')  { env.DOCKER_IMAGE_COMMIT  = parts[1] }
          if (parts[0] == 'DOCKER_IMAGE_LATEST') { env.DOCKER_IMAGE_LATEST = parts[1] }
          }
        }
      }
    }

    stage('Docker Push') {
      steps {
       script {
        docker.withRegistry('https://index.docker.io/v1/', 'dockerhub-creds') {
          powershell '''
            $ErrorActionPreference = "Stop"
            docker --version

            Write-Host "Pushing images to Docker Hub..."
            docker push $Env:DOCKER_IMAGE_COMMIT
            docker push $Env:DOCKER_IMAGE_LATEST
          '''
        }
      }
      }
    }

    stage('Deploy to Minikube') {
      when { expression { return env.DOCKER_IMAGE_LATEST } }
      steps {
        powershell '''
        $ErrorActionPreference = 'Stop'

        function Require-Cli($name) {
          if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
            Write-Error "$name not found in PATH"
            exit 1
          }
        }

        Require-Cli kubectl
        Require-Cli minikube

        Write-Host "Ensuring minikube is running..."
        minikube status *> $null
        if ($LASTEXITCODE -ne 0) {
          minikube start --memory=2048 --cpus=2
        }

        $commitTag = ($env:DOCKER_IMAGE_COMMIT.Split(':'))[-1]
        Write-Host "Deploying image tag: $commitTag"

        $yamlPath = 'k8s/aceest-fitness.yaml'
        if (-not (Test-Path $yamlPath)) {
          Write-Error "Missing $yamlPath"
          exit 1
        }

        $raw = Get-Content -Raw -Path $yamlPath

        # Avoid regex/backslashes: use literal contains/replace
        if (-not $raw.Contains('${IMAGE_TAG}')) {
          Write-Error "Placeholder ${IMAGE_TAG} not found in $yamlPath"
          exit 1
        }

        $rendered = $raw.Replace('${IMAGE_TAG}', $commitTag)

        $rendered | kubectl apply -f -

        Write-Host "Waiting for rollout..."
        kubectl rollout status deployment/aceest-fitness --timeout=180s

        Write-Host "Current deployed image:"
        kubectl get deploy aceest-fitness -o jsonpath="{.spec.template.spec.containers[0].image}"; Write-Host ""

        Write-Host "Service URL(s):"
        $nodeIp   = (minikube ip).Trim()
        $nodePort = (kubectl get svc aceest-fitness -o jsonpath="{.spec.ports[0].nodePort}" | Out-String).Trim()

        # Either of these two lines is fine:
        Write-Host ("http://{0}:{1}" -f $nodeIp, $nodePort)   # format operator (safest)
        # Write-Host "http://$($nodeIp):$($nodePort)"        # or sub-expressions
      '''
      }
    }
  }

  post {
    success  { echo 'Pipeline completed successfully.' }
    unstable { echo 'Pipeline marked unstable (possibly failed quality gate).' }
    failure  { echo 'Pipeline failed.' }
    always   { echo 'Build finished.' }
  }
}