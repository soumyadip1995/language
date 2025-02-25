import torch
from torch import nn
import math
import numpy as np 
import torch.nn.functional  as F
from math import sqrt


words = open(r"C:\Users\Soumyadip Nandi\Downloads\policy\language\text.txt", 'r' , encoding='utf-8').read().split()
# words[:20]


chars = sorted(list(set(words)))
string2integer = {ch: i for i, ch in enumerate(chars)}
# print(string2integer)

integer2string = {i:ch for ch,i in string2integer.items()}
encode = lambda s: [string2integer[c] for c in s]
# print(encode)

decode = lambda l: ''.join([integer2string[i] for i in l])
# print(decode)

data = torch.tensor(encode(words), dtype = torch.long)
# print(data)
# data.size()

## block_size and batch size has been changed from 64 and 512 to 32 and 128
block_size = 32
batch_size = 128
ix = torch.randint(len(data) - block_size, (batch_size,))

## hidden dimensionality has been changed from 512 to 128.

vocab_size = len(chars)
d_k = 128
token_emb = nn.Embedding(vocab_size, d_k)


x = torch.stack([data[i:i + block_size] for i in ix])
input_embeds = token_emb(x)
# input_embeds.size()


def scaled_dot_product(query, key, value):
  dim_k = query.size(-1)
  scores = torch.bmm(query, key.transpose(-2, -1)) / sqrt(dim_k)
  weights = F.softmax(scores, dim = -1)
  return torch.bmm(weights, value)

key = input_embeds
query = input_embeds
value = input_embeds

# sdp = scaled_dot_product(query, key, value)
# print(sdp.size())

### Multi headed attention

"""Having many heads allows the model to focus on different parts of the sentences. 
The softmax on one head tends to focus on one aspect of similarity. For example subject verb interaction."""
## A single attention head

class AttentionHead(nn.Module):
  def __init__(self, embedded_dim, head_dim):
    super().__init__()
    self.q = nn.Linear(embedded_dim, head_dim)
    self.k = nn.Linear(embedded_dim,  head_dim)
    self.v = nn.Linear(embedded_dim,  head_dim)

  def forward(self, x):
    attention_outputs = scaled_dot_product(self.q(x), self.k(x), self.v(x))
    

    return attention_outputs

# embedding_dim = embedding dimensions
# num_heads  = number of heads 


class MultiHeadAttention(nn.Module):
  def __init__(self, embedded_dim, num_heads):
    super().__init__()
    self.embedded_dim = embedded_dim
    self.num_heads = num_heads
    head_dim = embedded_dim // num_heads 

    self.heads = nn.ModuleList([AttentionHead(embedded_dim, head_dim) for _ in range(num_heads)])
    self.output_linear = nn.Linear(embedded_dim, embedded_dim)

  def forward(self, x):
    out = torch.cat([h(x) for h in self.heads], dim = -1)
    
    out = self.output_linear(out)

    return out

# multihead_attention = MultiHeadAttention(128, 8)
# # multihead_attention

# attention_outputs =  multihead_attention(input_embeds)
# # print(attention_outputs.size())


# from karpathy , partially
dropout = 0.2

class FeedForward(nn.Module):
  def __init__(self, embedded_dim):
    super(FeedForward, self).__init__()
    self.net = nn.Sequential(nn.Linear(embedded_dim, 4 * embedded_dim),
    nn.Linear(4 * embedded_dim, embedded_dim),
    nn.GELU(),
    nn.Dropout(dropout))

  def forward(self, x):
    return self.net(x)


### A simple Transformer Block    
class Transformer(nn.Module):
  def __init__(self, embedded_dim, num_heads):
    super(Transformer, self).__init__()
    self.attention = MultiHeadAttention(embedded_dim,  num_heads)
    self.feed_forward = FeedForward(embedded_dim)
    self.layer_norm_1 = nn.LayerNorm(embedded_dim)
    self.layer_norm_2 = nn.LayerNorm(embedded_dim)

  def forward(self, x):
    
    x = x + self.attention(self.layer_norm_1(x))
    x = x + self.feed_forward(self.layer_norm_2(x))
    return x

btt = Transformer(128, 8)
to = btt(input_embeds)
print(to.size())


