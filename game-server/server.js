const path = require('path');
const express = require('express');
const http = require('http');
const { Server } = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: '*',
  },
});

const STATIC_DIR = path.join(__dirname, 'public');

app.use(express.static(STATIC_DIR));

const players = {};
const rooms = {};

function normaliseUsername(username) {
  if (!username) return 'Player';
  const trimmed = String(username).trim();
  return trimmed.length > 0 ? trimmed : 'Player';
}

function initialGameState() {
  return {
    players: {},
    turn: null,
    turnName: null,
    gameOver: false,
    winner: null,
    winnerName: null,
  };
}

function serialiseRoom(room) {
  return {
    roomId: room.roomId,
    hostId: room.hostId,
    mode: room.mode,
    gameType: room.gameType,
    maxPlayers: room.maxPlayers,
    players: Object.fromEntries(
      Object.entries(room.players).map(([socketId, player]) => [socketId, { ...player }]),
    ),
  };
}

function computeWinnerName(room) {
  if (!room.gameState.gameOver || !room.gameState.winner) {
    room.gameState.winnerName = null;
    return;
  }

  const winnerColour = room.gameState.winner;
  const winnerSocketId = room.gameState.players?.[winnerColour];
  if (!winnerSocketId) {
    room.gameState.winnerName = winnerColour;
    return;
  }

  const name = players[winnerSocketId]?.username || room.players[winnerSocketId]?.name || 'Player';
  room.gameState.winnerName = name;
}

function emitGameState(roomId) {
  const room = rooms[roomId];
  if (!room) return;
  computeWinnerName(room);
  io.to(roomId).emit('gameStateUpdate', { ...room.gameState });
}

function broadcastLobby() {
  const availableRooms = Object.values(rooms).map((room) => serialiseRoom(room));
  io.emit('availableGames', availableRooms);
}

function removePlayerFromRoom(socket, roomId) {
  const room = rooms[roomId];
  if (!room) return;

  delete room.players[socket.id];
  if (room.gameState.players) {
    Object.keys(room.gameState.players).forEach((colour) => {
      if (room.gameState.players[colour] === socket.id) {
        room.gameState.players[colour] = null;
      }
    });
  }

  if (room.hostId === socket.id) {
    const remainingIds = Object.keys(room.players);
    room.hostId = remainingIds.length > 0 ? remainingIds[0] : null;
  }

  if (Object.keys(room.players).length === 0) {
    delete rooms[roomId];
  } else {
    io.to(roomId).emit('matchLobbyUpdate', serialiseRoom(room));
  }

  broadcastLobby();
}

function joinRoom(socket, roomId) {
  const room = rooms[roomId];
  if (!room) return;

  const player = players[socket.id] || { playerId: socket.id, inRoom: null, username: 'Player' };
  players[socket.id] = player;

  const name = player.username || 'Player';
  room.players[socket.id] = {
    playerId: socket.id,
    name,
    isReady: false,
  };
  player.inRoom = roomId;

  if (!room.hostId) {
    room.hostId = socket.id;
  }

  socket.join(roomId);

  socket.emit('roomJoined', serialiseRoom(room));
  io.to(roomId).emit('matchLobbyUpdate', serialiseRoom(room));
  broadcastLobby();
}

function startGame(roomId) {
  const room = rooms[roomId];
  if (!room) return;

  const playerIds = Object.keys(room.players);
  if (playerIds.length < 2) return;

  const [redPlayer, blackPlayer] = playerIds;

  room.gameState.players = {
    red: redPlayer,
    black: blackPlayer,
  };
  room.gameState.turn = 'red';
  room.gameState.turnName = room.players[redPlayer]?.name || 'Red';
  room.gameState.gameOver = false;
  room.gameState.winner = null;
  room.gameState.winnerName = null;

  io.to(roomId).emit('gameStateUpdate', { ...room.gameState });
}

io.on('connection', (socket) => {
  players[socket.id] = { playerId: socket.id, inRoom: null, username: 'Player' };
  broadcastLobby();

  socket.on('createGame', ({ gameType, mode, roomCode, username }) => {
    const player = players[socket.id] || { playerId: socket.id };
    player.username = normaliseUsername(username);
    player.inRoom = null;
    players[socket.id] = player;

    const roomId = mode === 'p2p' && roomCode ? roomCode : `room_${Math.random().toString(36).slice(2, 7)}`;

    rooms[roomId] = {
      roomId,
      hostId: socket.id,
      mode: mode || 'lan',
      gameType: gameType || 'Checkers',
      maxPlayers: 2,
      players: {},
      gameState: initialGameState(),
    };

    joinRoom(socket, roomId);
  });

  socket.on('joinGame', ({ roomId, username }) => {
    const room = rooms[roomId];
    if (!room) {
      socket.emit('error', 'Room is full or does not exist.');
      return;
    }
    if (Object.keys(room.players).length >= room.maxPlayers) {
      socket.emit('error', 'Room is full or does not exist.');
      return;
    }

    const player = players[socket.id] || { playerId: socket.id };
    player.username = normaliseUsername(username);
    player.inRoom = roomId;
    players[socket.id] = player;

    joinRoom(socket, roomId);
  });

  socket.on('toggleReady', ({ roomId }) => {
    const room = rooms[roomId];
    if (!room) return;
    const player = room.players[socket.id];
    if (!player) return;

    player.isReady = !player.isReady;
    io.to(roomId).emit('matchLobbyUpdate', serialiseRoom(room));

    const allReady =
      Object.keys(room.players).length === room.maxPlayers &&
      Object.values(room.players).every((p) => p.isReady);

    if (allReady) {
      startGame(roomId);
    }
  });

  socket.on('leaveRoom', ({ roomId }) => {
    const player = players[socket.id];
    if (player) {
      player.inRoom = null;
    }
    removePlayerFromRoom(socket, roomId);
    socket.leave(roomId);
  });

  socket.on('requestRematch', ({ roomId }) => {
    const room = rooms[roomId];
    if (!room) return;

    Object.values(room.players).forEach((p) => {
      p.isReady = false;
    });
    room.gameState = initialGameState();

    io.to(roomId).emit('matchLobbyUpdate', serialiseRoom(room));
    emitGameState(roomId);
  });

  socket.on('reportWinner', ({ roomId, winner }) => {
    const room = rooms[roomId];
    if (!room) return;
    if (!winner || !['red', 'black'].includes(winner)) return;

    room.gameState.gameOver = true;
    room.gameState.winner = winner;
    computeWinnerName(room);
    emitGameState(roomId);
  });

  socket.on('disconnect', () => {
    const player = players[socket.id];
    if (!player) return;

    const { inRoom } = player;
    if (inRoom) {
      removePlayerFromRoom(socket, inRoom);
    }

    delete players[socket.id];
    broadcastLobby();
  });
});

const PORT = process.env.PORT || 3000;

if (require.main === module) {
  server.listen(PORT, () => {
    // eslint-disable-next-line no-console
    console.log(`Server listening on port ${PORT}`);
  });
}

module.exports = { app, server, io, players, rooms };
