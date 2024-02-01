parallel (

	"conda":{
		node('linux_conda') {

			stage('init') {
			gitlabCommitStatus("init") {
				checkout scm
				}
			}

			stage('mamba') {
			gitlabCommitStatus("mamba") {
				sh "make install"
				}
			}

			stage('test') {
				gitlabCommitStatus("test") {
					echo "Running tests"
					sh "mamba run -n ctview make testing"
				}
			}

			stage('docker') {
				gitlabCommitStatus("docker") {
					sh "mamba run -n ctview make docker-build"
				}
			}
		}
	}
)