const connections = [[11,12],[11,13],[13,15],[12,14],[14,16],[11,23],[12,24],[23,24],[23,25],[25,27],[24,26],[26,28],[27,31],[28,32]];
export function createWebcamPose({ onStart, onStop, onPose }) {
  const button = document.querySelector('#webcamToggle'), panel = document.querySelector('#webcamPanel');
  const video = document.querySelector('#webcamVideo'), canvas = document.querySelector('#webcamOverlay');
  const status = document.querySelector('#webcamStatus'), mirror = document.querySelector('#webcamMirror');
  let active = false, generation = 0, worker, stream, timer, frameTimer, busy = false, lastVideo = -1;
  const ctx = canvas.getContext('2d');
  function message(text) { if (status.textContent !== text) status.textContent = text; }
  function stop(text = '', resume = true) {
    const wasActive = active;
    active = false; generation++; clearTimeout(timer); clearTimeout(frameTimer);
    worker?.terminate(); worker = null;
    stream?.getTracks().forEach(track => track.stop()); stream = null;
    video.pause(); video.srcObject = null; busy = false; lastVideo = -1;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    button.setAttribute('aria-pressed', 'false'); button.textContent = 'WEBCAM CONTROL';
    panel.hidden = !text; document.body.classList.remove('webcam-active');
    if (text) message(text);
    if (wasActive) onStop(resume);
  }
  function draw(points) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!points) return;
    ctx.strokeStyle = '#d5f3a5'; ctx.fillStyle = '#fff2d9'; ctx.lineWidth = 3;
    for (const [a, b] of connections) {
      if (points[a].visibility < .55 || points[b].visibility < .55) continue;
      ctx.beginPath(); ctx.moveTo(points[a].x * canvas.width, points[a].y * canvas.height); ctx.lineTo(points[b].x * canvas.width, points[b].y * canvas.height); ctx.stroke();
    }
    for (const p of points.slice(11)) if (p.visibility > .55) { ctx.beginPath(); ctx.arc(p.x * canvas.width, p.y * canvas.height, 4, 0, Math.PI * 2); ctx.fill(); }
  }
  async function frame(token) {
    if (!active || token !== generation) return;
    if (!busy && video.readyState >= 2 && video.currentTime !== lastVideo) {
      busy = true; lastVideo = video.currentTime;
      try {
        const bitmap = await createImageBitmap(video);
        if (!active || token !== generation) { bitmap.close(); return; }
        worker.postMessage({ type: 'frame', bitmap, timestamp: performance.now() }, [bitmap]);
        clearTimeout(timer); timer = setTimeout(() => stop('Tracking stopped responding. Try webcam control again.'), 12000);
      } catch { if (token === generation) stop('Could not read the camera. Try webcam control again.'); return; }
    }
    frameTimer = setTimeout(() => frame(token), 45);
  }
  async function start() {
    if (active) { stop(); return; }
    const token = ++generation;
    active = true; panel.hidden = false;
    button.setAttribute('aria-pressed', 'true'); button.textContent = 'STOP WEBCAM';
    document.body.classList.add('webcam-active');
    message('Allow camera access and keep your shoulders and arms visible.');
    try {
      if (!navigator.mediaDevices?.getUserMedia) throw new Error('unsupported');
      if (!onStart()) throw new Error('model');
      const camera = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 24, max: 30 } }, audio: false });
      if (!active || token !== generation) { camera.getTracks().forEach(t => t.stop()); return; }
      stream = camera; video.srcObject = stream;
      stream.getVideoTracks()[0].addEventListener('ended', () => { if (token === generation) stop('Camera disconnected. Connect a camera and try again.'); });
      await video.play();
      if (!active || token !== generation) return;
      canvas.width = video.videoWidth; canvas.height = video.videoHeight;
      message('Loading body tracking…');
      worker = new Worker(`${import.meta.env.BASE_URL}tracking/pose-worker.js`);
      worker.onerror = () => { if (token === generation) stop('Body tracking could not load. Refresh and try again.'); };
      worker.onmessage = ({ data }) => {
        if (!active || token !== generation) return;
        clearTimeout(timer);
        if (data.type === 'ready') { message('Show your shoulders and arms. Your upper body is enough.'); frame(token); }
        else if (data.type === 'pose') {
          busy = false; draw(data.landmarks);
          const tracked = onPose(data.world, mirror.checked, performance.now(), data.landmarks);
          message(tracked === 'upper' ? 'Upper body live · legs stay planted' : tracked ? 'Full body live · move your arms and legs' : 'Show your shoulders and arms to start tracking');
        } else if (data.type === 'error') stop('Body tracking could not start. Try webcam control again.');
      };
      timer = setTimeout(() => stop('Body tracking took too long to load. Try again.'), 45000);
      worker.postMessage({ type: 'init' });
    } catch (error) {
      if (token !== generation) return;
      const text = error.name === 'NotAllowedError' ? 'Camera access was blocked. Allow it in your browser settings, then try again.' : error.name === 'NotFoundError' ? 'No camera found. Connect a webcam and try again.' : error.name === 'NotReadableError' ? 'Camera is busy. Close other camera apps and try again.' : error.message === 'model' ? 'Wait for the mecha to finish loading, then try again.' : error.message === 'unsupported' ? 'Camera access is unavailable here. Open this page in Chrome or Safari over HTTPS.' : 'Camera could not start. Check its connection and try again.';
      stop(text);
    }
  }
  mirror.addEventListener('change', () => panel.classList.toggle('unmirrored', !mirror.checked));
  button.addEventListener('click', start);
  document.querySelector('#webcamClose').addEventListener('click', () => stop());
  document.addEventListener('visibilitychange', () => { if (document.hidden && active) stop(); });
  window.addEventListener('pagehide', () => stop('', false));
  return { start, stop, get active() { return active; } };
}
