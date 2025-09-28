async function fetchInfo() {
  const url = document.getElementById("urlInput").value;
  const res = await fetch("/get_info", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({url})
  });
  const data = await res.json();

  if (data.error) {
    alert("Error: " + data.error);
    return;
  }

  document.getElementById("videoPreview").style.display = "block";
  document.getElementById("videoTitle").innerText = data.title;
  document.getElementById("videoThumb").src = data.thumbnail;

  // Generate embed link for YouTube preview
  let videoId;
  if (data.url.includes("shorts/")) {
    videoId = data.url.split("shorts/")[1].split("?")[0];
  } else if (data.url.includes("v=")) {
    videoId = data.url.split("v=")[1].split("&")[0];
  }
  document.getElementById("videoPlayer").src = "https://www.youtube.com/embed/" + videoId;

  let formatSelect = document.getElementById("formatSelect");
  formatSelect.innerHTML = "";
  data.formats.forEach(f => {
    let opt = document.createElement("option");
    opt.value = f.format_id;
    opt.innerText = `${f.resolution} (${(f.filesize/1048576).toFixed(1)} MB)`;
    formatSelect.appendChild(opt);
  });

  loadHistory();
}

async function downloadVideo() {
  const url = document.getElementById("urlInput").value;
  const format_id = document.getElementById("formatSelect").value;
  const folder = document.getElementById("folderInput").value;

  const res = await fetch("/download", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({url, format_id, folder})
  });

  if (res.ok) {
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = window.URL.createObjectURL(blob);
    a.download = "video.mp4";
    a.click();
    loadHistory();
  } else {
    const err = await res.json();
    alert("Error: " + err.error);
  }
}

async function loadHistory() {
  const res = await fetch("/history");
  const history = await res.json();
  let list = document.getElementById("historyList");
  list.innerHTML = "";
  history.forEach(item => {
    let li = document.createElement("li");
    li.innerText = `${item.title} → saved at ${item.filepath}`;
    list.appendChild(li);
  });
}

loadHistory();
