/* MediaPipe runs off the rendering thread. Frames never leave this worker. */
importScripts('./runtime/vision_bundle.js');
let detector;
self.onmessage = async ({ data }) => {
  try {
    if (data.type === 'init') {
      const fileset = await Vision.FilesetResolver.forVisionTasks(new URL('./runtime/wasm/', self.location.href).href);
      detector = await Vision.PoseLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: new URL('./pose_landmarker_lite.task', self.location.href).href, delegate: 'CPU' },
        runningMode: 'VIDEO', numPoses: 1,
        minPoseDetectionConfidence: .55, minPosePresenceConfidence: .55, minTrackingConfidence: .55,
      });
      self.postMessage({ type: 'ready' });
    } else if (data.type === 'frame') {
      try {
        const result = detector.detectForVideo(data.bitmap, data.timestamp);
        self.postMessage({ type: 'pose', landmarks: result.landmarks[0], world: result.worldLandmarks[0] });
      } finally { data.bitmap.close(); }
    }
  } catch (error) { self.postMessage({ type: 'error', message: error.message }); }
};
