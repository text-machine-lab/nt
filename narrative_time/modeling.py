import torch
import torch.nn as nn

from transformers import AutoModel


class TransformerForRelationPrediction(nn.Module):
    def __init__(self, pretrained_model_name_or_path, num_relations):
        super().__init__()
        self.transformer = AutoModel.from_pretrained(pretrained_model_name_or_path)
        self.is_encoder_decoder = hasattr(self.transformer, "decoder")
        if self.is_encoder_decoder:
            del self.transformer.decoder

        hidden = self.transformer.config.hidden_size

        self.norm = nn.LayerNorm(hidden)
        # note that we divide randn by `hidden` and not `hidden ** 0.5`,
        # because it will be multiplied by transformer output twice,
        # thus the variance will be `hidden` instead of `hidden ** 0.5`
        self.W = nn.Parameter(torch.randn(num_relations, hidden, hidden) / hidden)
    
    @staticmethod
    def make_relation_logits(event_embeddings, W):
        event_embeddings = event_embeddings.unsqueeze(-3)  # (1, num_events, hidden)
        pre_logits = W @ event_embeddings.transpose(-1, -2)  # (num_rels, hidden, num_events_right)
        logits = event_embeddings @ pre_logits  # (1, num_events_left, hidden) @ (num_rels, hidden, num_events_right) -> (num_rels, num_events_left, num_events_right)
        logits = logits.permute(1, 2, 0)  # (num_events_left, num_events_right, num_rels)
        return logits

    def forward(self, input_ids, event_token_ids):
        if self.is_encoder_decoder:
            out = self.transformer.encoder(input_ids=input_ids.unsqueeze(0))
        else:
            out = self.transformer(input_ids=input_ids.unsqueeze(0))

        hidden_states = out.last_hidden_state.squeeze(0)
        hidden_states = self.norm(hidden_states)

        event_embeddings = hidden_states[event_token_ids, :]
        event_embeddings = self.norm(event_embeddings)
        relation_logits = self.make_relation_logits(event_embeddings, self.W)
        return relation_logits
