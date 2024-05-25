# see https://huey.readthedocs.io/en/latest/consumer.html
# see https://negativeepsilon.com/en/posts/huey-async-task-execution/


# django
from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task, task
from huey.contrib.djhuey import HUEY as huey
from django.utils import timezone

# python modules
from datetime import datetime
import os
import time
import traceback

# user modules
from lib.jr.jrfuncs import jrprint
from lib.jr import jrdfuncs
from hueyconfig import huey
from lib.hl import hlparser
from lib.jr import jrfuncs
















# module global funcs
@db_task()
def queueTaskBuildStoryPdf(game, requestOptions):

    # starting time of run
    timeStart = time.time()
    # start time of build
    buildDateStart = timezone.now()

    # reset
    buildLog = ""
    buildErrorStatus = False
    flagCleanAfter = True

    # options
    buildMode = requestOptions["buildMode"]

    # imports needing in function to avoid circular?
    from games.models import Game
    from games import gamefilemanager
    from games.gamefilemanager import GameFileManager

    # update model queue status before we start
    #game.queueStatus = Game.GameQueueStatusEnum_Running

    # save queu start status; we will update when we finish
    buildResultsPrevious = game.getBuildResults(buildMode)
    buildDateQueuedTimestamp = jrfuncs.getDictValueOrDefault(buildResultsPrevious, "buildDateQueued", None)
    buildDateQueued = jrdfuncs.convertTimeStampToDateTimeDefaultNow(buildDateQueuedTimestamp)
    #
    buildResults = {
        "queueStatus": Game.GameQueueStatusEnum_Running,
        "buildDateQueued": buildDateQueued.timestamp(),
        }
    game.setBuildResults(buildMode, buildResults)

    # save NOW early (and again later) since it will take some time and something else might run in meantime
    game.save()

    # properties
    gameModelPk = game.pk
    gameInternalName = game.name
    gameName = game.gameName
    gameText = game.text
    gameTextHash = game.textHash
    preferredFormatPaperSize = game.preferredFormatPaperSize
    preferredFormatLayout = game.preferredFormatLayout
    #
    # parsed values
    gameBuildVersion = game.version
    gameBuildVersionDate = game.versionDate

    # create new gamefilemanager; which will be intermediary for accessing game data
    gameFileManager = GameFileManager(game)


    # what outputs do we want parser to build/generate
    buildList = []
    if (buildMode in ["buildPreferred"]):
        # build preferred format
        build = {"label": "preferred format build", "gameName": gameName, "format": "pdf", "paperSize": preferredFormatPaperSize, "layout": preferredFormatLayout, "variant": "normal", "gameFileType": gamefilemanager.EnumGameFileTypeName_PreferredBuild, }
        addCalculatedFieldsToBuild(build)
        buildList.append(build)
        if (True):
            # build zip
            zipBuild = {"label": "zipping built files", "gameName": gameName, "variant": "zip", "layout": None, "gameFileType": gamefilemanager.EnumGameFileTypeName_PreferredBuild}
            buildList.append(zipBuild)
    if (buildMode in ["buildDebug"]):
        # build debug format
        build = {"label": "debug build", "gameName": gameName, "format": "pdf", "paperSize": preferredFormatPaperSize, "layout": preferredFormatLayout, "variant": "debug", "gameFileType": gamefilemanager.EnumGameFileTypeName_Debug, }
        addCalculatedFieldsToBuild(build)
        buildList.append(build)
        if (True):
            # build zip
            zipBuild = {"label": "zipping built files", "gameName": gameName, "variant": "zip", "layout": None, "gameFileType": gamefilemanager.EnumGameFileTypeName_Debug}
            buildList.append(zipBuild)
    if (buildMode in ["buildDraft"]):
        # build complete list; all combinations of page size and layout
        buildList += generateCompleteBuildList(game, False)
        if (True):
            # build zip
            zipBuild = {"label": "zipping built files", "gameName": gameName, "variant": "zip", "layout": None, "gameFileType": gamefilemanager.EnumGameFileTypeName_DraftBuild}
            buildList.append(zipBuild)
        #
    if (buildMode not in ["buildPreferred", "buildDebug", "buildDraft"]):
        raise Exception("Build mode not understood: '{}'.".format(buildMode))
    
    # initialize the directory of files, deleting any that exist previously
    gameFileManager.deleteFilesInBuildListDirectories(buildList)

    # create options
    hlDirPath = os.path.abspath(os.path.dirname(__file__))
    optionsDirPath = hlDirPath + "/options"
    dataDirPath = hlDirPath + "/hldata"
    templateDirPath = hlDirPath + "/templates"
    overrideOptions = {
        "hlDataDir": dataDirPath,
        "templatedir": templateDirPath,
        "buildList": buildList,
        "gameFileManager": gameFileManager,
        }
        


    # DO THE ACTUAL BUILD
    # this may take a long time to run (minutes)

    # start the build log
    buildLog = "Building: '{}'...\n".format(buildMode)

    try:
        # create hl parser
        hlParser = hlparser.HlParser(optionsDirPath, overrideOptions)

        # parse text
        hlParser.parseStoryTextIntoBlocks(gameText, 'hlweb2')

        # run pdf generation
        retv = hlParser.runBuildList(flagCleanAfter)
    
    except Exception as e:
        #msg = "ERROR: Exception while building storybook. Exception = " + str(e)
        #msg = "ERROR: Exception while building storybook. Exception = " + traceback.format_exc(e)
        msg = "ERROR: Exception while building storybook. Exception = " + repr(e)
        msg += "; " + traceback.format_exc()
        jrprint(msg)
        buildLog += msg
        buildErrorStatus = True


    # add file generated list
    generatedFileList = hlParser.getGeneratedFileList()
    if (len(generatedFileList)>0):
        if (buildLog != ""):
            buildLog += "\n\n-----\n\n"
        buildLog += "Generated file list:\n" + "\n".join(generatedFileList)


    # now store result in game model instance gameModelPk
    buildErrorStatus = (buildErrorStatus or hlParser.getBuildErrorStatus())
    buildLogParser = hlParser.getBuildLog()
    if (buildLogParser != ""):
        if (buildLog != ""):
            buildLog += "\n\n-----\n\n"
        buildLog += "Parser Build Log:\n" + buildLogParser



    # elapsed time
    # ATTN: this needs rewriting
    timeEnd = time.time()
    timeSecs = timeEnd - timeStart
    timeStr = jrfuncs.niceElapsedTimeStrMinsSecs(timeSecs)
    # wait time
    waitSecs = (timezone.now().timestamp() - buildDateQueued.timestamp())
    #waitSecs = (timezone.now() - buildDateQueued).total_seconds()
    waitStr = jrfuncs.niceElapsedTimeStrMinsSecs(waitSecs)
    #
    buildLog += "\nActual build time: {}.".format(timeStr)
    buildLog += "\nBuild wait time: {}.".format(waitStr)


    # REload game instance AGAIN to save state, in case it has changed
    from games.models import Game
    game = Game.objects.get(pk=gameModelPk)
    if (game is None):
        raise Exception("Failed to find game pk={} for updating build results - stage 2.".format(gameModelPk))
        # can't continue below


    # ATTN: a nice sanity check here would be to see if game text has changed
    # ATTN: we may not need to do this anymore, as long as we report when displaying that text hash has changed so its out of date
    if (False) and (game.textHash != gameTextHash):
        # ERROR
        buildErrorStatus = True
        buildLog = "ERROR: Game model text modified by author during build; needs rebuild."


    # update build status with results of build, AND with the version we actually built (which may go out of date later)
    buildDateEnd = timezone.now()
    buildResults = {
        "queueStatus": Game.GameQueueStatusEnum_Errored if (buildErrorStatus) else Game.GameQueueStatusEnum_Completed,
        "buildDateQueued": buildDateQueued.timestamp(),
        "buildDateStart": buildDateStart.timestamp(),
        "buildDateEnd": buildDateEnd.timestamp(),
        "buildVersion": gameBuildVersion,
        "buildVersionDate": gameBuildVersionDate,
        "buildTextHash": gameTextHash,
        "buildError": buildErrorStatus,
        "buildLog": buildLog,
    }

    # set build results buildlog
    game.setBuildResults(buildMode, buildResults)

    # log
    # jrprint("Updated model game {} after completion of queueTaskBuildStoryPdf with queuestats = {}.".format(gameModelPk, game.queueStatus))

    # result for instant run
    if (buildErrorStatus):
        retv = "Errors during build"
    else:
        retv = "Build was successful"
        # update lead stats on successful build
        game.leadStats = hlParser.getLeadStats()["summaryString"]
    #

    # save game
    game.save()

    return retv







def generateCompleteBuildList(game, flagDebugIncluded):
    # loop twice, the first time just calculate buildCount
    # imports needing in function to avoid circular?
    from games.models import Game
    from games import gamefilemanager

    buildList = []
    index = 0
    buildCount = 0
    # summary and debug
    buildCount += 1
    if (flagDebugIncluded):
        buildCount += 1
    # customs
    buildCount += 1
    #
    preferredFormatPaperSize = game.preferredFormatPaperSize
    preferredFormatLayout = game.preferredFormatLayout
    # properties
    gameInternalName = game.name
    gameName = game.gameName
    gameFileType = gamefilemanager.EnumGameFileTypeName_DraftBuild
    #
    if (True):
        # customs
        index += 1
        build = {"label": "SOLOPRN_LETTER_LargeFont", "gameName": gameName, "suffix": "_SOLOPRN_LETTER_LargeFont", "format": "pdf", "paperSize": Game.GamePreferredFormatPaperSize_Letter, "layout": Game.GamePreferredFormatLayout_Solo, "variant": "normal", "fontSize": "16pt", "gameFileType": gameFileType, }
        addCalculatedFieldsToBuild(build)
        buildList.append(build)

    if (True):
        # programmatic
        for stage in ["precount","run"]:
            for paperSize in Game.GameFormatPaperSizeCompleteList:
                for layout in Game.GameFormatLayoutCompleteList:
                    # skip certain configurations
                    columns = calcColumnsFromLayout(layout)
                    maxColumns = calcMaxColumnsFromPaperSize(paperSize)
                    if (columns>maxColumns):
                        # skip it
                        continue
                    if (stage=="precount"):
                        buildCount += 1
                        continue
                    # add the build
                    index += 1
                    label = "complete build {} of {} ({} x {})".format(index, buildCount, layout, paperSize)
                    #
                    build = {"label": label, "gameName": gameName, "format": "pdf", "paperSize": paperSize, "layout": layout, "variant": "normal", "gameFileType": gameFileType, }
                    addCalculatedFieldsToBuild(build)
                    buildList.append(build)

    # also debug, in preferred format
    if (flagDebugIncluded):
        index += 1
        label = "complete build {} of {} (debug)".format(index, buildCount)
        build = {"label": label, "gameName": gameName, "format": "pdf", "paperSize": preferredFormatPaperSize, "layout": preferredFormatLayout, "variant": "debug", "gameFileType": gameFileType, }
        addCalculatedFieldsToBuild(build)
        buildList.append(build)
    #
    # summary in letter format
    index += 1
    label = "complete build {} of {} (summary)".format(index, buildCount)
    paperSize = Game.GamePreferredFormatPaperSize_Letter
    #
    build = {"label": label, "gameName": gameName, "format": "pdf", "paperSize": paperSize, "layout": Game.GamePreferredFormatLayout_Solo, "variant": "summary", "gameFileType": gameFileType, }
    addCalculatedFieldsToBuild(build)
    buildList.append(build)

    return buildList
# ---------------------------------------------------------------------------















# ---------------------------------------------------------------------------
def publishGameFiles(game):
    # imports needing in function to avoid circular?
    from games.models import Game, calculateGameFilePathRuntime
    from games import gamefilemanager
    from games.gamefilemanager import GameFileManager

    # create new gamefilemanager; which will be intermediary for accessing game data
    gameFileManager = GameFileManager(game)
    
    # publish files
    publishErrored = False
    currentDate = timezone.now()
    try:
        publishResult = gameFileManager.copyPublishFiles(gamefilemanager.EnumGameFileTypeName_DraftBuild, gamefilemanager.EnumGameFileTypeName_Published)
    except Exception as e:
        msg = "ERROR: Exception while trying to copy publish files. Exception = " + repr(e)
        msg += "; " + traceback.format_exc()
        jrprint(msg)
        publishResult = msg
        publishErrored = True

    if (not publishErrored):
        # update states and save
        publishResult = "Successfully published"
        game.publishDate = currentDate

    # update
    # this is different from build, we are essentially copying from draft
    overrideResults = {
        "publishResult": publishResult,
        "publishErrored": publishErrored,
        "publishDate": currentDate.timestamp(),
        }
    game.copyBuildResults("published", "buildDraft", overrideResults)

    # save
    game.save()

    return publishResult
# ---------------------------------------------------------------------------







# ---------------------------------------------------------------------------
def checkBuildFiles(buildDir, buildList):
    errorMessage = ""
    for build in buildList:
        filePathBuild = buildDir + "/" + build["gameName"] + build["suffix"] + ".pdf"
        if (not jrfuncs.pathExists(filePathBuild)):
            errorMessage += "Missing file '{}'.\n".format(filePathBuild)
    if (errorMessage!=""):
        return errorMessage
    return None


def publishBuildFiles(buildDir, buildList, publishDir):
    errorMessage = ""
    for build in buildList:
        filePathBuild = buildDir + "/" + build["gameName"] + build["suffix"] + ".pdf"
        if (not jrfuncs.pathExists(filePathBuild)):
            errorMessage += "Missing file '{}'.\n".format(filePathBuild)
        else:
            filePathPublish = publishDir + "/" + build["gameName"] + build["suffix"] + ".pdf"
            jrfuncs.copyFilePath(filePathBuild, filePathPublish)
    if (errorMessage!=""):
        return errorMessage
    return None
# ---------------------------------------------------------------------------























# ---------------------------------------------------------------------------
# helpers


def addCalculatedFieldsToBuild(build):
    paperSize = build["paperSize"]
    layout = build["layout"]
    #
    fontSize = build['fontSize'] if ('fontSize' in build) else calcFontSizeFromPaperSize(paperSize)
    paperSizeLatex = build['paperSizeLatex'] if ('paperSizeLatex' in build) else calcPaperSizeLatexFromPaperSize(paperSize)
    doubleSided = build['doubleSided'] if ('doubleSided' in build) else calcDoubledSidednessFromLayout(layout)
    columns = build['columns'] if ('columns' in build) else calcColumnsFromLayout(layout)
    solo = build['solo'] if ('solo' in build) else calcSoloFromLayout(layout)
    #
    if ("suffix" not in build):
        suffix = calcBuildNameSuffixForVariant(build)
        build["suffix"] = suffix
    build["fontSize"] = fontSize
    build["paperSizeLatex"] = paperSizeLatex
    build["doubleSided"] = doubleSided
    build["columns"] = columns
    build["solo"] = solo



def calcBuildNameSuffixForVariant(build):
    label = build["label"]
    format = build["format"]
    paperSize = build["paperSize"]
    layout = build["layout"]
    buildVariant = build["variant"]    
    #
    if (buildVariant=="normal"):
        suffix = "_{}_{}".format(layout, paperSize)
    elif (buildVariant=="debug"):
        suffix = "_{}_{}_{}".format("debug", layout, paperSize)
    elif (buildVariant=="summary"):
        suffix = "_summary"
    else:
        raise Exception("Variant mode '{}' not understood in runBuildList for label '{}'".format(buildVariant, label))
    #
    return suffix



def calcFontSizeFromPaperSize(paperSize):
    # imports needing in function to avoid circular?
    from games.models import Game
    #
    paperSizeToFontMap = {
        Game.GamePreferredFormatPaperSize_Letter: "10pt",
        Game.GamePreferredFormatPaperSize_A4: "10pt",
        Game.GamePreferredFormatPaperSize_B5: "8pt",
        Game.GamePreferredFormatPaperSize_A5: "8pt",            
    }
    return paperSizeToFontMap[paperSize]


def calcPaperSizeLatexFromPaperSize(paperSize):
    # imports needing in function to avoid circular?
    from games.models import Game
    #
    paperSizeToLatexPaperSizeMap = {
        Game.GamePreferredFormatPaperSize_Letter: "letter",
        Game.GamePreferredFormatPaperSize_A4: "a4",
        Game.GamePreferredFormatPaperSize_B5: "b5",
        Game.GamePreferredFormatPaperSize_A5: "a5",            
    }
    return paperSizeToLatexPaperSizeMap[paperSize]


def calcDoubledSidednessFromLayout(layout):
    # imports needing in function to avoid circular?
    from games.models import Game
    #
    layoutToDoubleSidednessMap = {
        Game.GamePreferredFormatLayout_Solo: False,
        Game.GamePreferredFormatLayout_SoloPrint: True,
        Game.GamePreferredFormatLayout_OneCol: True,
        Game.GamePreferredFormatLayout_TwoCol: True,            
    }
    return layoutToDoubleSidednessMap[layout]


def calcColumnsFromLayout(layout):
    # imports needing in function to avoid circular?
    from games.models import Game
    #
    layoutToColumnsMap = {
        Game.GamePreferredFormatLayout_Solo: 1,
        Game.GamePreferredFormatLayout_SoloPrint: 1,
        Game.GamePreferredFormatLayout_OneCol: 1,
        Game.GamePreferredFormatLayout_TwoCol: 2,            
    }
    return layoutToColumnsMap[layout]


def calcSoloFromLayout(layout):
    # imports needing in function to avoid circular?
    from games.models import Game
    #
    layoutToSoloMap = {
        Game.GamePreferredFormatLayout_Solo: True,
        Game.GamePreferredFormatLayout_SoloPrint: True,
        Game.GamePreferredFormatLayout_OneCol: False,
        Game.GamePreferredFormatLayout_TwoCol: False,
    }
    return layoutToSoloMap[layout]


def calcMaxColumnsFromPaperSize(paperSize):
    # imports needing in function to avoid circular?
    from games.models import Game
    #
    paperSizeToMaxColumnsMap = {
        Game.GamePreferredFormatPaperSize_Letter: 2,
        Game.GamePreferredFormatPaperSize_A4: 2,
        Game.GamePreferredFormatPaperSize_B5: 2,
        Game.GamePreferredFormatPaperSize_A5: 1,            
    }
    return paperSizeToMaxColumnsMap[paperSize]
# ---------------------------------------------------------------------------
