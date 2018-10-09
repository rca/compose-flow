@Library('OpenSlateProd')_  // https://github.com/openslate/jenkins-shared-library

def customPublishTask = {
    cf env.DEPLOY_ENV, 'compose build --pull'
    sh "compose-flow -e ${env.DEPLOY_ENV} --project-name ${env.REPO_NAME} task publish"
}

def publishWhen = { env.TAG_NAME }

openslatePipeline {
    mentions = '@roberto <@marcusian>'
    deployEnv = 'prod'
    lint = true
    test = true
    publish = publishWhen
    publishFunction = customPublishTask
    deploy = false
}
