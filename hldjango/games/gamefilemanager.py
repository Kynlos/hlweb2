# this helper class helps work with game "files", whether they are images, or built pdfs, etc.

# python modules
import os
import datetime

# django modules
from django.conf import settings

# helpers
from lib.jr import jrfuncs
from lib.jr.jrfuncs import jrprint
from lib.jr.jrfilefinder import JrFileFinder






# ---------------------------------------------------------------------------
# game file type info
# each will have their own subdirectory in media/ directory
EnumGameFileTypeName_StoryUpload = "uploadsStory"
#
EnumGameFileTypeName_DraftBuild = "buildDraft"
EnumGameFileTypeName_PreferredBuild = "buildPreferred"
EnumGameFileTypeName_Debug = "buildDebug"
#
EnumGameFileTypeName_Published = "published"
#
EnumGameFileTypeName_VersionedGame = "versionedGameText"


# enum for game file type
GameFileTypeDbFieldChoices = [
    (EnumGameFileTypeName_StoryUpload, "Story upload (image, etc.)"),
    (EnumGameFileTypeName_DraftBuild, "Build draft file"),
    (EnumGameFileTypeName_PreferredBuild, "Preferred built file"),
    (EnumGameFileTypeName_Published, "Published file"),
    (EnumGameFileTypeName_VersionedGame, "Versioned game text file"),
    (EnumGameFileTypeName_Debug, "Debug file"),
]
# ---------------------------------------------------------------------------










# helper
def calculateGameFilePathRuntime(game, subdir, flagRelative):
    gamePk = game.pk
    if (flagRelative):
        path = "/".join(["games", str(gamePk), subdir])
    else:
        path = "/".join([str(settings.MEDIA_ROOT), "games", str(gamePk), subdir])
    path = jrfuncs.canonicalFilePath(path)
    return path

def calculateGameFileUploadPathRuntimeRelative(instance, filename):
    basePath = calculateGameFilePathRuntime(instance.game, EnumGameFileTypeName_StoryUpload, True)
    path = "/".join([basePath, filename])
    path = jrfuncs.canonicalFilePath(path)
    return path

def calculateAbsoluteMediaPathForRelativePath(relativePath):
    path = "/".join([str(settings.MEDIA_ROOT), relativePath])
    path = jrfuncs.canonicalFilePath(path)
    return path















class GameFileManager:
    def __init__(self, inGame):
        self.game = inGame
        self.imageFileFinder = None


    def initImageFileFinderIfNeeded(self):
        if (self.imageFileFinder is None):
            # create image file helper
            imageFileFinderOptions = {"stripExtensions": False}
            self.imageFileFinder = JrFileFinder(imageFileFinderOptions)
            self.imageFileFinder.clearExtensionList()
            self.imageFileFinder.addExtensionListImages()
            # now scan
            imageDirectoryList = []
            # add uploads directory for this game
            imageDirectoryList.append({'prefix':'', 'path':self.getDirectoryPathForGameType(EnumGameFileTypeName_StoryUpload)})
            # add shared media file directory
            imageDirectoryList.append({'prefix':'shared/images', 'path': self.getSharedImageDirectory()})
            self.imageFileFinder.setDirectoryList(imageDirectoryList)
            self.imageFileFinder.scanDirs(False)

        return self.imageFileFinder


    def buildFileList(self, gameFileTypeName):
        # build a list of dictionary items for files in a given section
        # there are two possibilities here:
        # 1. files as represented by GameFile model entries in the database; this would be especially important if we need to store extra data with a file; or if we are using some distributed cloud based file serving
        # 2. files on a local drive, which we dont have to keep track of other than doing a file searching
        # different game types might be stored differently?
        return self.buildFileListFromLocalDrivePath(gameFileTypeName)


    def buildFileListFromLocalDrivePath(self, gameFileTypeName):
        dirPath = self.getDirectoryPathForGameType(gameFileTypeName)
        urlBase = self.getBaseUrlPathForGameType(gameFileTypeName)
        #
        flist = []
        if (not jrfuncs.directoryExists(dirPath)):
            return flist
        for fileName in os.listdir(dirPath):
            # should we filter on extension?
            if (True):
                filePath = os.path.join(dirPath, fileName)
                url = urlBase + "/" + fileName
                # use mtime modification time to get original creation date on file copy
                fileTimestamp = os.path.getmtime(filePath)
                fileDateTime = datetime.datetime.fromtimestamp(fileTimestamp)
                fileDateString = jrfuncs.getNiceDateTimeCompact(fileDateTime)
                fileSizeBytes = os.path.getsize(filePath)
                fileSizeNiceStr = jrfuncs.niceFileSizeStr(fileSizeBytes)
                fileEntry = {
                    "name": fileName,
                    "path": filePath,
                    "comment": "",
                    "url": url,
                    "fileTimestamp": fileTimestamp,
                    "fileDateTime": fileDateTime,
                    "fileDateString": fileDateString,
                    "fileSizeBytes": fileSizeBytes,
                    "fileSizeNiceStr": fileSizeNiceStr,
                    }
                flist.append(fileEntry)
        #
        #jrprint("buildFileListFromLocalDrivePath -> game {} type {} = path: {}; found {} files.".format(self.game.name, gameFileTypeName, dirPath, len(flist)))
        #
        return flist


    def buildFileListFromDb(self, gameFileTypeName):
        # build list from database
        return []





    def deleteAllFilesForGameType(self, gameFileTypeName):
        # delete all the files of the game file type
        self.deleteAllFilesForGameTypeInDb(gameFileTypeName)
        self.deleteAllFilesForGameTypeOnLocalDrive(gameFileTypeName)

    def deleteAllFilesForGameTypeOnLocalDrive(self, gameFileTypeName):
        # delete all the files of the game file type
        fileList = self.buildFileListFromLocalDrivePath(gameFileTypeName)
        # now walk and delete
        for fileEntry in fileList:
            filePath = fileEntry["path"]
            #jrprint("ATTN: deleteAllFilesForGameTypeOnLocalDrive deleting file '{}'.".format(filePath))
            jrfuncs.deleteFilePathIfExists(filePath)

    def deleteAllFilesForGameTypeInDb(self, gameFileTypeName):
        # delete all the files of the game file type
        return

    



    def notifyNewFileCreatedForGameType(self, gameFileTypeName, filePath, extraFields):
        # a new file was created; we might here add a db entry OR create an auxiliary file with extraFields, OR do nothing
        jrprint("notifyNewFileCreatedForGameType ->  file added to game {} of type {} with path '{}' and fields: {}.".format(self.game.name, gameFileTypeName, filePath, extraFields))





    def getDirectoryPathForGameType(self, gameFileTypeName):
        # return the directory file path where game files of this type are stored
        gamePk = self.game.pk
        subdir = gameFileTypeName
        filePath = "/".join([str(settings.MEDIA_ROOT), "games", str(gamePk), subdir])
        filePath = jrfuncs.canonicalFilePath(filePath)
        return filePath

    def getMediaSubDirectoryPathForGameType(self, gameFileTypeName):
        # return the relative media directory file path where game files of this type are stored
        gamePk = self.game.pk
        subdir = gameFileTypeName
        filePath = "/".join(["games", str(gamePk), subdir])
        filePath = jrfuncs.canonicalFilePath(filePath)
        return filePath

    def getSharedImageDirectory(self):
        filePath = str(settings.JR_DIR_SHAREDIMAGES)
        filePath = jrfuncs.canonicalFilePath(filePath)
        return filePath


    def getBaseUrlPathForGameType(self, gameFileTypeName):
        # return the url base path where game files of this type are stored
        gamePk = self.game.pk
        subdir = gameFileTypeName        
        urlPath = "/".join([str(settings.MEDIA_URL), "games", str(gamePk), subdir])
        return urlPath


    def prepareEmptyFileDirectoryForGameType(self, gameFileTypeName):
        # delete any files in directory, create directory if needed
        self.deleteAllFilesForGameType(gameFileTypeName)
        self.createFileDirectoryForGameTypeIfNeeded(gameFileTypeName)
    

    def createFileDirectoryForGameTypeIfNeeded(self, gameFileTypeName):
        dirPath = self.getDirectoryPathForGameType(gameFileTypeName)
        jrfuncs.createDirIfMissing(dirPath)



    # image finder proxies
    def findImagesForName(self, name, flagMarkUsage, flagRevertToPrefix):
        # hand off to imageFileFinder
        self.initImageFileFinderIfNeeded()
        return self.imageFileFinder.findImagesForName(name, flagMarkUsage, flagRevertToPrefix)



    # helper to clear out directories before building in them
    def deleteFilesInBuildListDirectories(self, buildList):
        uniqueGameTypesToBuild = []
        for abuild in buildList:
            variant = abuild["variant"]
            if (variant=="zip"):
                # variant zip is special
                continue
            gtype = abuild["gameFileType"]
            if (gtype not in uniqueGameTypesToBuild):
                uniqueGameTypesToBuild.append(gtype)
        for gtype in uniqueGameTypesToBuild:
            self.prepareEmptyFileDirectoryForGameType(gtype)




    def copyPublishFiles(self, fromGameType, toGameType):
        # raise exception on error; otherwise return text message describing results

        # source directory
        fromDir = self.getDirectoryPathForGameType(fromGameType)
        if (not jrfuncs.directoryExists(fromDir)):
            raise Exception("The source directory to copy from does not exist: '{}'.".format(fromDir))
        
        # source file list
        fromFileFile = self.buildFileList(fromGameType)
        if (len(fromFileFile)==0):
            raise Exception("No files found in source directory to copy from does: '{}'.".format(fromDir)) 

        # destination
        toDir = self.getDirectoryPathForGameType(toGameType)
        self.prepareEmptyFileDirectoryForGameType(toGameType)

        # ok now copy files
        fileCopyCount = 0
        for fileEntry in fromFileFile:
            filePathSource = fileEntry["path"]
            fileName = os.path.basename(filePathSource)
            fileExt = os.path.splitext(fileName)[1]
            if (fileExt==".zip"):
                # for zip file we do a substitue in filename
                fileName = fileName.replace(fromGameType, toGameType)
            filePathDest = os.path.join(toDir, fileName)
            jrfuncs.copyFilePath(filePathSource, filePathDest)
            fileCopyCount += 1
        
        resultMessage = "Successfully copied ({}) files from {} to {}.".format(fileCopyCount, fromGameType, toGameType)
        return resultMessage


