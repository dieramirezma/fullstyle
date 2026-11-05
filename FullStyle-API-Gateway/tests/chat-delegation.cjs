const test = require('node:test');
const assert = require('node:assert/strict');
const axios = require('axios');
const { ChatAPI } = require('../dist/datasources/chatAPI');
const { chatResolvers } = require('../dist/graphql/resolvers/chat');

test('chat forwards caller token through the resolver and preserves input', async () => {
  const original = axios.post;
  const calls = [];
  axios.post = async (...args) => {
    calls.push(args);
    return { data: { reply: 'ok', session_id: 'same' } };
  };
  try {
    const input = { message: 'hello', session_id: 'same' };
    const response = await chatResolvers.Mutation.sendMessage(null, input, {
      token: 'Bearer caller',
    });
    assert.equal(response.reply, 'ok');
    assert.equal(calls.length, 1);
    assert.ok(calls[0][0].endsWith('/api/v1/chat/send'));
    assert.deepEqual(calls[0][1], input);
    assert.equal(calls[0][2].headers.Authorization, 'Bearer caller');
  } finally {
    axios.post = original;
  }
});

test('missing identity cannot reach upstream', async () => {
  const original = axios.post;
  let calls = 0;
  axios.post = async () => {
    calls++;
    throw new Error('must not call upstream');
  };
  try {
    await assert.rejects(
      new ChatAPI().sendMessage({ message: 'write' }, ''),
      /Failed to send message/,
    );
    assert.equal(calls, 0);
  } finally {
    axios.post = original;
  }
});
