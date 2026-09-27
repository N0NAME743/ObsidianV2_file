### ChangeTitle_MarkdownFile
##  GoogleDriveのアカウントは「RV」を利用

# v1.00 
#   ・ファイルの更新日を元にMarkdown形式のファイルを参照し、＃行の内容をタイトル行と判定
#   ・タイトル行が見当たらない場合は、除外対象とし、ログファイルへ出力
# v2.00　更新の判断に時間ではなく、ファイルサイズでを用いるように修正
# v2.01　サブフォルダの検索はコメントアウト
# v2.10　ファイル更新の判断を時間ではなく文字数に変更
# v3.00　ファイルのスキップ処理の内容を適切に動作するように修正

function renameAndCopyMarkdownFiles() {
  var sourceFolderId = '1IweVZV3FCjXIJD5gPtXaHIt-1y0EOBOR'; // 元のフォルダ（General Space）のIDを指定
  var destinationFolderId = '1HkeiXu9-mgLLouYJrXLH4r-p-1_qBYNC'; // 出力先のフォルダ（modified）のIDを指定
 
  var sourceFolder = DriveApp.getFolderById(sourceFolderId);
  var destinationFolder = DriveApp.getFolderById(destinationFolderId);
  
  var lastExecutionFile = getOrCreateLastExecutionFile(destinationFolder);
  var lastExecutionData;

  try {
    var lastExecutionContent = lastExecutionFile.getBlob().getDataAsString();
    lastExecutionData = JSON.parse(lastExecutionContent);
    Logger.log('前回の実行データ: ' + JSON.stringify(lastExecutionData));
  } catch (error) {
    Logger.log('エラーが発生しました。空のデータを使用します。エラー: ' + error.message);
    lastExecutionData = {};
  }
  
  var currentExecutionData = {};
  var results = processFolder(sourceFolder, destinationFolder, lastExecutionData, currentExecutionData);
  var searchFileCount = results.searchFileCount;
  var skipFileCount = results.skipFileCount;

  // 最後に currentExecutionData を lastExecutionFile に保存
  lastExecutionFile.setContent(JSON.stringify(currentExecutionData));
  Logger.log('検索ファイル数（.mdのみ）: ' + searchFileCount + '｜スキップ数: ' + skipFileCount);
}

function processFolder(folder, destinationFolder, lastExecutionData, currentExecutionData) {
  var files = folder.getFiles();
  var searchFileCount = 0;
  var skipFileCount = 0;

  var notesFileName = 'Notes_without_markdown.md';
  var notesFile;

  var existingFiles = destinationFolder.getFilesByName(notesFileName);
  if (existingFiles.hasNext()) {
    notesFile = existingFiles.next();
    Logger.log('既存のノートファイルを使用: ' + notesFile.getName());
  } else {
    notesFile = destinationFolder.createFile(notesFileName, '');
    Logger.log('新しいノートファイルを作成: ' + notesFile.getName());
  }

  var notesBlob = notesFile.getBlob();
  var notesContent = notesBlob.getDataAsString();

  while (files.hasNext()) {
    var file = files.next();

    if (!file.getName().endsWith('.md')) {
      continue;
    }

    searchFileCount++;

    var fileId = file.getId();
    var content = file.getBlob().getDataAsString();
    var charCount = content.length;
    var lastCharCount = lastExecutionData[fileId];

    Logger.log('ファイル名: ' + file.getName());
    Logger.log('現在の文字数: ' + charCount + ' | 前回の文字数: ' + (lastCharCount !== undefined ? lastCharCount : 'なし'));

    if (lastCharCount !== undefined && lastCharCount === charCount) {
      Logger.log('文字数が前回実行時と同じためスキップ: ' + file.getName());
      skipFileCount++;

      // スキップされたファイルも currentExecutionData に追加
      currentExecutionData[fileId] = lastCharCount; 
      continue;
    }

    currentExecutionData[fileId] = charCount;

    Logger.log('処理中のファイル: ' + file.getName());

    var lines = content.split('\n');
    var title = '';

    for (var i = 0; i < lines.length; i++) {
      if (lines[i].trim().startsWith('#')) {
        title = lines[i].trim();
        break;
      }
    }

    if (title) {
      var newFileName = title.replace(/#/g, '').trim().replace(/ /g, "_") + '.md';
      var existingDestinationFiles = destinationFolder.getFilesByName(newFileName);
      if (existingDestinationFiles.hasNext()) {
        var existingFile = existingDestinationFiles.next();
        existingFile.setContent(content);
        Logger.log('既存のファイルを上書きしました: ' + existingFile.getName());
      } else {
        var newFile = destinationFolder.createFile(newFileName, content);
        Logger.log('ファイルが ' + newFile.getName() + ' として ' + destinationFolder.getName() + ' に作成されました。');
      }
    } else {
      var timestamp = new Date();
      var formattedTime = Utilities.formatDate(timestamp, Session.getScriptTimeZone(), 'yyyy-MM-dd_HH:mm');
      var notesEntry = formattedTime + ' (' + file.getName() + '): タイトル行が見つかりませんでした。\n';
      notesContent += notesEntry;
      Logger.log('タイトル行が見つからなかったため、ノートファイルにエントリを追加: ' + notesEntry.trim());
    }
  }

  notesFile.setContent(notesContent);

  return {
    searchFileCount: searchFileCount,
    skipFileCount: skipFileCount
  };
}

function getOrCreateLastExecutionFile(destinationFolder) {
  var fileName = 'lastExecutionTime.txt';
  var existingFiles = destinationFolder.getFilesByName(fileName);
  
  if (existingFiles.hasNext()) {
    return existingFiles.next();
  } else {
    var newFile = destinationFolder.createFile(fileName, '{}');
    Logger.log('新しい実行時刻ファイルを作成: ' + newFile.getName());
    return newFile;
  }
}
