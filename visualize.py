import numpy as np
import pygame
import cv2

from utils import pickle_load
from utils import pickle_save


class RawVisualizer:
  def __init__(self, load_prefix):
    self.color_path = load_prefix + '_color.avi'
    self.color_src = cv2.VideoCapture(self.color_path)
    self.color_height = int(self.color_src.get(cv2.CAP_PROP_FRAME_HEIGHT))
    self.color_width = int(self.color_src.get(cv2.CAP_PROP_FRAME_WIDTH))

    self.depth_path = load_prefix + '_depth.pkl'
    self.depth_frames = pickle_load(self.depth_path)
    self.depth_height = self.depth_frames[0].shape[0]
    self.depth_width = self.depth_frames[0].shape[1]

    self.body_path = load_prefix + '_body.pkl'
    self.body_frames = pickle_load(self.body_path)

    self.fps = 30
    self.playing = True
    self.frame_idx = 0

    pygame.init()
    self.surface = pygame.Surface(
        (self.color_width + self.depth_width, self.color_height), 0, 24
    )
    self.hw_ratio = self.surface.get_height() / self.surface.get_width()

    # screen layout: # is color stream, * is depth, & is body index
    #  ----------------------
    # |################# *****|
    # |################# *****|
    # |################# *****|
    # |################# &&&&&|
    # |################# &&&&&|
    # |################# &&&&&|
    #  ----------------------
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
          self.playing = not self.playing

      if self.playing:
        ret, color = self.color_src.read()
        depth = self.depth_frames[self.frame_idx]
        body = self.body_frames[self.frame_idx]
        self.frame_idx += 1

        if self.frame_idx == len(self.depth_frames):
          self.frame_idx = 0

        self.frame[:, :self.color_width] = np.flip(
          color, axis=-1
        ).astype(np.uint8)
        self.frame[:self.depth_height, -self.depth_width:] = np.repeat(
          depth[:, :, np.newaxis] / 4500 * 255, 3, axis=2
        ).astype(np.uint8)
        self.frame[-self.depth_height:, -self.depth_width:] = np.repeat(
          255 - body[:, :, np.newaxis], 3, axis=2
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

        print(self.clock.get_fps())
      self.clock.tick(self.fps)

    pygame.quit()


if __name__ == '__main__':
  v = RawVisualizer('test')
  v.run()