import numpy as np
from pykinect2 import PyKinectRuntime
from pykinect2 import PyKinectV2
import pygame
import cv2

from utils import pickle_load
from utils import pickle_save


class KinectRecorder:
  def __init__(self, save_prefix, visualize, save_on_record):
    self.kinect = PyKinectRuntime.PyKinectRuntime(
      PyKinectV2.FrameSourceTypes_Depth |
      PyKinectV2.FrameSourceTypes_Color |
      PyKinectV2.FrameSourceTypes_BodyIndex
    )
    self.depth_height = self.kinect.depth_frame_desc.Height
    self.depth_width = self.kinect.depth_frame_desc.Width
    self.color_height = self.kinect.color_frame_desc.Height
    self.color_width = self.kinect.color_frame_desc.Width
    self.body = np.zeros([self.depth_height, self.depth_width])
    self.color = np.zeros([self.color_height, self.color_width, 3])
    self.depth = np.zeros([self.depth_height, self.depth_width])
    self.color_cap = None
    self.color_frames = []
    self.depth_frames = []
    self.body_frames = []
    self.fps = 30
    self.recording = False
    self.visualize = visualize
    self.save_prefix = save_prefix
    self.save_on_record = save_on_record
    self.min_fps = 30

    pygame.init()
    self.surface = pygame.Surface(
      (self.color_width + self.depth_width, self.color_height), 0, 24
    )
    self.hw_ratio = self.surface.get_height() / self.surface.get_width()

    scale = 0.6
    self.screen = pygame.display.set_mode(
      (
        int(self.surface.get_width() * scale),
        int(self.surface.get_height() * scale)
      ),
      pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE,
      24
    )
    self.done = False
    self.clock = pygame.time.Clock()
    pygame.display.set_caption('Kinect Human Recorder')

    self.frame = np.ones([
      self.surface.get_height(),
      self.surface.get_width(),
      3
    ])

  def run(self):
    while not self.done:
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          self.done = True
        elif event.type == pygame.VIDEORESIZE:
          self.screen = pygame.display.set_mode(
            event.dict['size'],
            pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE,
            24
          )
        elif event.type == pygame.KEYDOWN:
          if self.recording:
            pass
          else:
            self.recording = True
            pygame.display.set_caption('Kinect Human Recorder - Recording')
            if self.save_on_record:
              self.color_cap = cv2.VideoWriter(
                self.save_prefix + '_color.avi',
                cv2.VideoWriter_fourcc(*'DIVX'),
                self.fps,
                (self.color_width, self.color_height)
              )

      self.color = self.kinect.get_last_color_frame()
      self.color = np.reshape(
          self.color,
          [self.color_height, self.color_width, -1]
      )
      self.color = self.color[..., :3]

      self.depth = self.kinect.get_last_depth_frame()
      self.depth = np.reshape(
          self.depth,
          [self.depth_height, self.depth_width]
      )

      self.body = self.kinect.get_last_body_index_frame()
      self.body = np.reshape(
          self.body,
          [self.depth_height, self.depth_width]
      )

      if self.recording:
        self.depth_frames.append(self.depth)
        self.body_frames.append(self.body)
        if self.color_cap is not None:
          self.color_cap.write(self.color)
        else:
          self.color_frames.append(self.color)

      if self.visualize:
        self.frame[:, :self.color_width] = np.flip(
          self.color, axis=-1
        ).astype(np.uint8)
        self.frame[:self.depth_height, -self.depth_width:] = np.repeat(
            self.depth[:, :, np.newaxis] / 4500 * 255, 3, axis=2
        ).astype(np.uint8)
        self.frame[-self.depth_height:, -self.depth_width:] = np.repeat(
            255 - self.body[:, :, np.newaxis], 3, axis=2
        ).astype(np.uint8)
        pygame.surfarray.blit_array(
          self.surface, np.transpose(self.frame, axes=[1, 0, 2])
        )
        target_height = int(self.hw_ratio * self.screen.get_width())
        surface_to_draw = pygame.transform.scale(
            self.surface, (self.screen.get_width(), target_height)
        )
        self.screen.blit(surface_to_draw, (0, 0))
        surface_to_draw = None
        pygame.display.update()
        pygame.display.flip()

      fps = self.clock.get_fps()
      if fps != 0 and fps < self.min_fps:
        self.min_fps = fps
      self.clock.tick(self.fps)

    pygame.quit()

    if self.color_cap is None:
      self.color_cap = cv2.VideoWriter(
        self.save_prefix + '_color.avi',
        cv2.VideoWriter_fourcc(*'DIVX'),
        self.fps,
        (self.color_width, self.color_height)
      )
      for frame in self.color_frames:
        self.color_cap.write(frame)

    self.color_cap.release()

    pickle_save(self.save_prefix + '_depth.pkl', self.depth_frames)
    pickle_save(self.save_prefix + '_body.pkl', self.body_frames)

    print('Minimal FPS: %f' % self.min_fps)


if __name__ == '__main__':
  save_prefix = input('Please input the path to save recorded data: ')
  kr = KinectRecorder(save_prefix, False, False)
  kr.run()