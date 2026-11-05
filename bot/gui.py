"""gui.py - the "Bot Vision" window (Feature B).

This is a pygame window that shows the board exactly as the bot sees it,
highlights every legal move, and draws an arrow for the move the bot chose.
It is also reused by Feature A (playing a position read from a screenshot).

Beginner notes:
  * pygame draws to a "screen" (a window). We draw shapes/fonts onto it,
    then call pygame.display.flip() to make everything visible.
  * A "Rect" is just a rectangle (x, y, width, height).
  * We map chess squares (a1..h8) to pixel positions ourselves.
"""
from __future__ import annotations

import math
import os

import chess

# Unicode chess glyphs. Upper-case = white, lower-case = black.
GLYPHS = {
    "K": "\u2654", "Q": "\u2655", "R": "\u2656",
    "B": "\u2657", "N": "\u2658", "P": "\u2659",
    "k": "\u265A", "q": "\u265B", "r": "\u265C",
    "b": "\u265D", "n": "\u265E", "p": "\u265F",
}


class BoardView:
    """A pygame window that visualizes a chess position."""

    def __init__(
        self,
        square_size: int = 64,
        flip: bool = False,
        title: str = "Chess Bot Vision",
        headless: bool = False,
    ):
        # headless=True is used by tests: draw without opening a real window.
        if headless:
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
            os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

        # Import pygame here (not at the top) so unrelated code doesn't
        # need pygame installed just because this file exists.
        import pygame

        self.pygame = pygame
        pygame.init()

        self.square = square_size
        self.flip = flip
        self.closed = False
        self.margin = 28          # border around the board
        self.info_height = 84     # strip under the board for text
        self.board_px = square_size * 8
        self.width = self.board_px + self.margin * 2
        self.height = self.board_px + self.margin * 2 + self.info_height

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(title)

        # --- Colours ---------------------------------------------------
        self.background = (24, 24, 24)
        self.light_square = (238, 238, 210)
        self.dark_square = (118, 150, 86)
        self.text_color = (235, 235, 235)
        self.from_tint = (255, 215, 0, 80)      # highlight origin squares
        self.dot_color = (20, 20, 20)
        self.arrow_color = (0, 140, 255)
        self.threat_tint = (220, 40, 40, 80)   # red wash on threatened squares
        self.threat_ring = (220, 40, 40)

        # --- Fonts -----------------------------------------------------
        # Try a font that actually has chess glyphs (Windows has this one).
        glyph_font_path = (
            pygame.font.match_font("segoeuisymbol")
            or pygame.font.match_font("seguisym")
            or pygame.font.match_font("symbola")
        )
        self.use_glyphs = glyph_font_path is not None
        self.piece_font = pygame.font.Font(glyph_font_path, int(square_size * 0.78))
        self.letter_font = pygame.font.Font(None, int(square_size * 0.5))
        self.info_font = pygame.font.Font(None, 22)
        self.big_font = pygame.font.Font(None, 46)
        self.lobby_font = pygame.font.Font(None, 26)

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------
    def _square_to_rect(self, square: int):
        """Return the pygame.Rect (pixels) for a chess square."""
        file = chess.square_file(square)   # 0..7  (a..h)
        rank = chess.square_rank(square)   # 0..7  (1..8)
        if self.flip:
            col, row = 7 - file, rank
        else:
            col, row = file, 7 - rank
        x = self.margin + col * self.square
        y = self.margin + row * self.square
        return self.pygame.Rect(x, y, self.square, self.square)

    def _is_dark(self, square: int) -> bool:
        # a1 is a dark square. (file + rank) even -> dark.
        return (chess.square_file(square) + chess.square_rank(square)) % 2 == 0

    # ------------------------------------------------------------------
    # Drawing pieces
    # ------------------------------------------------------------------
    def _draw_piece(self, piece: chess.Piece, rect):
        pg = self.pygame
        symbol = piece.symbol()
        if self.use_glyphs:
            glyph = GLYPHS[symbol]
            shadow = self.piece_font.render(glyph, True, (25, 25, 25))
            colour = (250, 250, 250) if piece.color == chess.WHITE else (20, 20, 20)
            fill = self.piece_font.render(glyph, True, colour)
            self.screen.blit(
                shadow, shadow.get_rect(center=(rect.centerx + 1, rect.centery + 1))
            )
            self.screen.blit(fill, fill.get_rect(center=rect.center))
        else:
            # Fallback: a coloured disc with a letter (always readable).
            radius = int(self.square * 0.40)
            disc = (245, 245, 245) if piece.color == chess.WHITE else (35, 35, 35)
            text = (25, 25, 25) if piece.color == chess.WHITE else (245, 245, 245)
            pg.draw.circle(self.screen, disc, rect.center, radius)
            pg.draw.circle(self.screen, (0, 0, 0), rect.center, radius, 1)
            label = self.letter_font.render(symbol.upper(), True, text)
            self.screen.blit(label, label.get_rect(center=rect.center))

    def _draw_arrow(self, move: chess.Move):
        pg = self.pygame
        start = self._square_to_rect(move.from_square).center
        end = self._square_to_rect(move.to_square).center
        width = max(3, self.square // 12)
        pg.draw.line(self.screen, self.arrow_color, start, end, width)

        dx, dy = end[0] - start[0], end[1] - start[1]
        length = math.hypot(dx, dy) or 1
        ux, uy = dx / length, dy / length
        head_len = self.square * 0.35
        head_w = self.square * 0.18
        base = (end[0] - ux * head_len, end[1] - uy * head_len)
        left = (base[0] - uy * head_w, base[1] + ux * head_w)
        right = (base[0] + uy * head_w, base[1] - ux * head_w)
        pg.draw.polygon(self.screen, self.arrow_color, [end, left, right])

    def _draw_info(self, board: chess.Board, info: str):
        side = "White" if board.turn == chess.WHITE else "Black"
        line1 = f"{side} to move   |   move {board.fullmove_number}"
        surf1 = self.info_font.render(line1, True, self.text_color)
        y = self.margin + self.board_px + 10
        self.screen.blit(surf1, (self.margin, y))

        if info:
            surf2 = self.info_font.render(info, True, self.arrow_color)
            self.screen.blit(surf2, (self.margin, y + 26))

    # ------------------------------------------------------------------
    # Main entry: draw one frame
    # ------------------------------------------------------------------
    def show(
        self,
        board: chess.Board,
        moves=None,
        chosen_move: chess.Move | None = None,
        info: str = "",
        threat_squares=None,
    ) -> bool:
        """Draw the whole scene, flip it to the screen, and pump events.

        moves          - the moves to show as dots (usually ONE piece's moves)
        chosen_move    - the move to draw as an arrow
        threat_squares - squares to mark in red ("threats" against us)

        Returns True while the window is open, False once it was closed.
        """
        if self.closed:
            return False

        pg = self.pygame
        self.screen.fill(self.background)
        moves = list(moves) if moves is not None else []
        threat_squares = list(threat_squares) if threat_squares else []

        # 1) the 8x8 squares
        for square in chess.SQUARES:
            rect = self._square_to_rect(square)
            colour = self.dark_square if self._is_dark(square) else self.light_square
            pg.draw.rect(self.screen, colour, rect)

        # 2) red wash on threatened squares (under the pieces)
        if threat_squares:
            overlay = pg.Surface((self.width, self.height), pg.SRCALPHA)
            for square in threat_squares:
                overlay.fill(self.threat_tint, self._square_to_rect(square))
            self.screen.blit(overlay, (0, 0))

        # 3) a golden tint on the square the moving piece starts from
        if moves:
            overlay = pg.Surface((self.width, self.height), pg.SRCALPHA)
            for move in moves:
                overlay.fill(self.from_tint, self._square_to_rect(move.from_square))
            self.screen.blit(overlay, (0, 0))

        # 4) the pieces
        for square, piece in board.piece_map().items():
            self._draw_piece(piece, self._square_to_rect(square))

        # 5) red rings on threatened pieces (drawn over them so they stand out)
        for square in threat_squares:
            pg.draw.rect(self.screen, self.threat_ring, self._square_to_rect(square), 3)

        # 6) dots on the destinations of the piece being played
        for move in moves:
            rect = self._square_to_rect(move.to_square)
            pg.draw.circle(
                self.screen, self.dot_color, rect.center, int(self.square * 0.16)
            )

        # 7) the chosen move as an arrow
        if chosen_move is not None:
            self._draw_arrow(chosen_move)

        # 8) the info strip
        self._draw_info(board, info)

        pg.display.flip()

        # Keep the window responsive without blocking.
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.closed = True
        return not self.closed

    def show_lobby(self, title: str, lines) -> bool:
        """Draw the 'Waiting for a game' lobby screen. Returns False if closed."""
        if self.closed:
            return False

        pg = self.pygame
        self.screen.fill((16, 16, 22))

        heading = self.big_font.render(title, True, (245, 245, 245))
        self.screen.blit(heading, heading.get_rect(center=(self.width // 2, 80)))

        y = 150
        for line in lines:
            surf = self.lobby_font.render(str(line), True, (200, 200, 215))
            self.screen.blit(surf, surf.get_rect(center=(self.width // 2, y)))
            y += 34

        hint = self.lobby_font.render("Ctrl-C to quit", True, (120, 120, 130))
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, self.height - 30)))

        pg.display.flip()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.closed = True
        return not self.closed

    def close(self) -> None:
        """Close the window and shut pygame down."""
        self.closed = True
        self.pygame.quit()
