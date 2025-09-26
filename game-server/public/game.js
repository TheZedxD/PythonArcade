/* eslint-disable no-undef */
const socket = io();

const usernameInput = document.getElementById('username-input');

const mainLobbyEls = {
  view: document.getElementById('main-lobby'),
  gameSelection: document.getElementById('game-selection'),
  joinOnlineBtn: document.getElementById('join-online-btn'),
  roomCodeInput: document.getElementById('room-code-input'),
};

const matchLobbyEls = {
  view: document.getElementById('match-lobby'),
  player1Card: document.getElementById('player-card-1'),
  player2Card: document.getElementById('player-card-2'),
  player1Status: document.querySelector('#player-card-1 .player-status'),
  player2Status: document.querySelector('#player-card-2 .player-status'),
  readyBtn: document.getElementById('ready-btn'),
  leaveBtn: document.getElementById('leave-room-btn'),
};

const gameEls = {
  view: document.getElementById('game-view'),
  turnIndicator: document.getElementById('turn-indicator'),
  gameBoard: document.getElementById('game-board'),
  gameOverMessage: document.getElementById('game-over-message'),
  winnerText: document.getElementById('winner-text'),
  playAgainBtn: document.getElementById('play-again-btn'),
};

let currentRoomId = null;
let games = [];

function showView(view) {
  [mainLobbyEls.view, matchLobbyEls.view, gameEls.view].forEach((section) => {
    if (!section) return;
    if (section === view) {
      section.classList.remove('hidden');
    } else {
      section.classList.add('hidden');
    }
  });
}

function getUsername() {
  const value = usernameInput?.value?.trim();
  return value && value.length > 0 ? value : null;
}

function populateGameSelection() {
  if (!mainLobbyEls.gameSelection) return;
  mainLobbyEls.gameSelection.innerHTML = '';

  games = [
    {
      name: 'Checkers',
      description: 'Classic Checkers played online.',
    },
  ];

  games.forEach((game) => {
    const card = document.createElement('div');
    card.className = 'game-card';

    const title = document.createElement('h3');
    title.textContent = game.name;

    const description = document.createElement('p');
    description.textContent = game.description;

    const createBtn = document.createElement('button');
    createBtn.textContent = 'Create Match';
    createBtn.addEventListener('click', () => {
      socket.emit('createGame', {
        gameType: game.name,
        mode: 'lan',
        username: getUsername(),
      });
    });

    card.appendChild(title);
    card.appendChild(description);
    card.appendChild(createBtn);
    mainLobbyEls.gameSelection.appendChild(card);
  });
}

function resetLobbyCards() {
  const cards = [matchLobbyEls.player1Card, matchLobbyEls.player2Card];
  cards.forEach((card) => {
    if (!card) return;
    card.classList.remove('filled');
    const name = card.querySelector('.player-name');
    const status = card.querySelector('.player-status');
    if (name) name.textContent = 'Waiting for player...';
    if (status) status.textContent = 'Not Ready';
  });
}

function updateMatchLobby(room) {
  if (!room || !room.players) return;

  resetLobbyCards();

  const playerIds = Object.keys(room.players);
  if (playerIds.length === 0) return;

  const p1 = room.players[playerIds[0]];
  if (p1) {
    matchLobbyEls.player1Card.classList.add('filled');
    matchLobbyEls.player1Card.querySelector('.player-name').textContent = `${p1.name}${
      playerIds[0] === room.hostId ? ' (Host)' : ''
    }`;
    matchLobbyEls.player1Status.textContent = p1.isReady ? 'Ready' : 'Not Ready';
  }

  if (playerIds.length > 1) {
    const p2 = room.players[playerIds[1]];
    if (p2) {
      matchLobbyEls.player2Card.classList.add('filled');
      matchLobbyEls.player2Card.querySelector('.player-name').textContent = `${p2.name}${
        playerIds[1] === room.hostId ? ' (Host)' : ''
      }`;
      matchLobbyEls.player2Status.textContent = p2.isReady ? 'Ready' : 'Not Ready';
    }
  }
}

function joinGame(roomId) {
  socket.emit('joinGame', {
    roomId,
    username: getUsername(),
  });
}

// Socket events
socket.on('connect', () => {
  populateGameSelection();
});

socket.on('availableGames', (rooms) => {
  games = rooms || [];
  if (!Array.isArray(games)) return;
  mainLobbyEls.gameSelection.innerHTML = '';
  games.forEach((room) => {
    const card = document.createElement('div');
    card.className = 'game-card';

    const title = document.createElement('h3');
    title.textContent = `${room.gameType} – ${room.roomId}`;

    const info = document.createElement('p');
    info.textContent = `${Object.keys(room.players).length}/${room.maxPlayers} players`;

    const joinBtn = document.createElement('button');
    joinBtn.textContent = 'Join';
    joinBtn.disabled = Object.keys(room.players).length >= room.maxPlayers;
    joinBtn.addEventListener('click', () => joinGame(room.roomId));

    card.appendChild(title);
    card.appendChild(info);
    card.appendChild(joinBtn);
    mainLobbyEls.gameSelection.appendChild(card);
  });
});

socket.on('roomJoined', (room) => {
  currentRoomId = room.roomId;
  updateMatchLobby(room);
  showView(matchLobbyEls.view);
});

socket.on('matchLobbyUpdate', (room) => {
  if (!room || room.roomId !== currentRoomId) return;
  updateMatchLobby(room);
});

socket.on('gameStateUpdate', (gameState) => {
  if (!gameState) return;
  if (gameState.turn) {
    gameEls.turnIndicator.textContent = `${gameState.turnName ?? gameState.turn} to move`;
  }

  if (gameState.gameOver) {
    const name = gameState.winnerName || gameState.winner || 'Player';
    gameEls.winnerText.textContent = `${name} Wins!`;
    gameEls.gameOverMessage.classList.remove('hidden');
  }
});

socket.on('error', (message) => {
  // eslint-disable-next-line no-console
  console.error('Server error:', message);
});

// UI events
mainLobbyEls.joinOnlineBtn?.addEventListener('click', () => {
  const roomCode = mainLobbyEls.roomCodeInput?.value?.trim();
  if (!roomCode) return;
  socket.emit('createGame', {
    gameType: 'Checkers',
    mode: 'p2p',
    roomCode,
    username: getUsername(),
  });
});

matchLobbyEls.readyBtn?.addEventListener('click', () => {
  if (!currentRoomId) return;
  socket.emit('toggleReady', { roomId: currentRoomId });
});

matchLobbyEls.leaveBtn?.addEventListener('click', () => {
  if (!currentRoomId) return;
  socket.emit('leaveRoom', { roomId: currentRoomId });
  currentRoomId = null;
  showView(mainLobbyEls.view);
});

gameEls.playAgainBtn?.addEventListener('click', () => {
  if (!currentRoomId) return;
  socket.emit('requestRematch', { roomId: currentRoomId });
  gameEls.gameOverMessage.classList.add('hidden');
});

// expose joinGame for debugging
window.joinGame = joinGame;
