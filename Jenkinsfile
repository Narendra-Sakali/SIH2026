pipeline {

    agent any

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out SIH2026 project...'

                git branch: 'main',
                    url: 'https://github.com/Narendra-Sakali/SIH2026.git'
            }
        }

        stage('Python Setup') {
            steps {
                echo 'Checking Python installation...'

                bat 'python --version'
                bat 'pip --version'
            }
        }

        stage('Install Dependencies') {
            steps {
                echo 'Installing Python dependencies...'

                bat 'python -m pip install --upgrade pip'
                bat 'pip install -r requirements.txt'
            }
        }

        stage('Application Check') {
            steps {
                echo 'Checking FastAPI application...'

                bat 'python -c "from main import app; print(app.title)"'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo 'Building Docker image...'

                bat 'docker build -t sih2026:latest .'
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying application...'

                bat 'docker rm -f sih2026-container || exit 0'

                bat 'docker run -d --name sih2026-container -p 8000:8000 sih2026:latest'
            }
        }

        stage('Health Check') {
            steps {
                echo 'Checking application health...'

                bat 'timeout /t 10'

                bat 'curl http://localhost:8000/health'
            }
        }
    }

    post {

        success {
            echo '================================='
            echo 'CI/CD PIPELINE SUCCESSFUL'
            echo 'Application deployed successfully'
            echo '================================='
        }

        failure {
            echo '================================='
            echo 'CI/CD PIPELINE FAILED'
            echo 'Check Jenkins console output'
            echo '================================='
        }
    }
}
