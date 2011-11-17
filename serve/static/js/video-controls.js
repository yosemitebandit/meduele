// iframe api example from http://code.google.com/apis/youtube/iframe_api_reference.html

// asynch load of iframe
var tag = document.createElement('script');
tag.src = "https://www.youtube.com/player_api";
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

// create an iframe and the youtube player
var player;
function onYouTubePlayerAPIReady() {
  player = new YT.Player('video-modal', {
    height: '480',
    width: '853',
    videoId: 'q_gSaW4sj6I',
  });
}
