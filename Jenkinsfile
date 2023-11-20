#!groovy
@Library('PSL@LKG')
@Library('fusion-psl@v4')
@Library('fusion-pipeline-configuration')

def downloadClangStaticChecker() {
    echo "Download clang-static-analyzer"
    
    clangAnalyzerPkgSrc = "team-fusion360-generic/breBuildTools/clang-static-analyzer.tar.gz"
    clangAnalyzerPkg = "clang-static-analzer.tar.gz"
    
    artifactory.download(
        clangAnalyzerPkgSrc,
        clangAnalyzerPkg
    )
    
    echo "Untar the static analzer"
    sh "tar xf ${clangAnalyzerPkg}"
}

def checkoutClientDelivery(String commitId = "develop") {
    echo "Download and checkout client-delivery"
    def repoUrl = "https://git.autodesk.com/fusion/client-delivery.git"
    dir('client-delivery')
    {
        common.checkoutCommit(repoUrl, commitId)
        systemShell(script: "git clean -xffd")
    }
}

def setupClientDelivery() {
    echo "Configuring client-delivery"
    dir('client-delivery')
    {
        sh """
            export _NEUTRON_PROJECT_OPTIONS='-DCMAKE_OSX_ARCHITECTURES=x86_64 -DCMAKE_EXPORT_COMPILE_COMMANDS=YES'
            ./Build/Central/Mac/GenerateNinja.command Release
        """
    }
}

def getPRCommit(prId) {
    def repoPath = "fusion/client-delivery"
    def content = github.api.getPullRequestById(repoPath, prId)
    sha = content['head']['sha']
    baseSha = content['base']['sha']
    return ['sha': sha, 'baseSha': baseSha]
}

// we run dsau on a filtered compile_commands.json that doesn't have the files from Output/MAC64
def dsau() {
    // Build Command
    command = """
            rm -rf virtual_env
            pwd
            ls
            mkdir virtual_env
            python3 -m venv virtual_env
            source ./virtual_env/bin/activate
            pip install requests

    """

    // Build command
    command = command + "python main.py " 
    command = command + "--f360=client-delivery "
    command = command + "--scanner=clang-static-analyzer "
    command = command + "--cmds=client-delivery/Output/MAC64/compile_commands.json "

    command = command + "--header-filter-regex='^(.*\\/3P\\/.*)' "
    command = command + "--ignore-paths=/client-delivery/Output/MAC64/ "

    command = command + "--update-dashboard=${params.UPDATE_DASHBOARD} "

    if (params.PR_OR_BRANCH == 'pr') {
        result = getPRCommit(params.PR_ID)
        sha = result['sha']
        baseSha = result['baseSha']
        cwd = pwd()

        // Export diff as a file
        sh """
            cd client-delivery
            git diff -U0 ${baseSha}...${sha} --output ../pr.diff
        """

        // Add PR commands
        command = command + "--scan-pr=${cwd}/pr.diff"
    }
    else {
        // Additional branch commands
    }

    // Execute command
    echo command
    sh command
}

def getTestEnvironment() {
  def envlist = []
  withCredentials([file(credentialsId: 'dashboard_credentials', variable: 'ENV_FILE')]){
    def envFile = readFile(ENV_FILE);
    def envPairs = envFile.split('\n');
    for (int i = 0; i < envPairs.size(); i++) {
      def envItem = envPairs[i];
      if (envItem.length() > 0 && envItem.indexOf('=') > 0 && !envItem.startsWith('#') ) {
        envlist.add(envItem);
      }
    }

    // Uncomment the below lines code to see the CLIENT_ID and CLIENT_SECRET of the Token use in Jenkins.
    // CLIENT_ID and CLIENT_SECRET are required to debug DSAU locally
    /*def props = readProperties file: env.ENV_FILE
    def clientId = props['CLIENT_ID']
    def clientSecret = props['CLIENT_SECRET']

    println('client id: ' + clientId)
    println('client secret: ' + clientSecret)*/
  }

  return envlist
}

def uploadDatabaseToArtifactory() {
    echo "Uploading database to artifactory"
    artifactory.upload(
        pattern: "test.db",
        target: "team-fusion360-temp/breBuildTools/test.db",
        props: "",
        description: "Ocurrences database"
    )
}

def setBuildName() {
    def buildName = BUILD_NUMBER
    echo "Set build"
    if (params.PR_OR_BRANCH == 'branch') {
        if (params.BRANCH_NAME == '') {
            buildName = "develop-${BUILD_NUMBER}"
        }
        else {
            buildName = "${params.BRANCH_NAME}-${BUILD_NUMBER}"
        }
    }  else {
        buildName = "${params.PR_OR_BRANCH}-${params.PR_ID}-${BUILD_NUMBER}"
    }

    buildName = "client-delivery" + '-' + buildName

    echo "set displayName to ${buildName}"
    currentBuild.displayName = buildName
    return
}

pipeline {

    agent {
        node {
            label pipelineConfig.agents.mac.standard
            customWorkspace common.customWorkspace
        }
    }
	
	triggers {
		cron('TZ=US/Pacific\nH 17 * * *')
	}
	
    options {
        timeout(time: 10, unit: 'HOURS')
        timestamps()
    }
    parameters {
        choice(
            name: 'PR_OR_BRANCH',
            choices: ['branch', 'pr'],
            description: 'Branch or Pull Request'
        )
        string(
            name: 'BRANCH_NAME',
            defaultValue: '',
            description: 'client-delivery branch name, ex. develop, ' +
                'leave it blank if it\'s for Pull Request'
        )
        string(
            name: 'PR_ID',
            defaultValue: '',
            description: 'client-delivery Pull Request ID, ex. 10704, ' +
                'leave it blank if it\'s for branch'
        )
        booleanParam(
            name: 'UPDATE_DASHBOARD',
            defaultValue: true,
            description: 'Upload statistics to Governance Dashboard'
        )
    }
    stages {
        stage('Set Build Name') {
            steps {
                setBuildName()
            }
        }
        stage("Checkout") {
            steps {
                script {
                    deleteDir()
                    checkout scm 
                }
            }
        }
        stage('Fetching clang static analyzer scanner') {
            steps {
                downloadClangStaticChecker()
            }
        }
        stage('client-delivery Checkout') {
            steps {
                checkoutClientDelivery()
            }
        }
        stage('client-delivery setup') {
            steps {
                setupClientDelivery()
            }
        }
        stage('Running DSAU') {
            steps {
                withEnv(getTestEnvironment()){
                    dsau()
                }
            }
        }
        stage('Upload database to artifactory'){
            steps{
                uploadDatabaseToArtifactory()
            }
        }
    }
    post{
        // always cleanup
        always{
            deleteDir()
        }
    }
}