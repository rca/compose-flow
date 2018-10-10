@Library('OpenSlateProd')_  // https://github.com/openslate/jenkins-shared-library

def customPublishTask = {
    cfPublish()
    cf env.DEPLOY_ENV, 'task publish'
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
