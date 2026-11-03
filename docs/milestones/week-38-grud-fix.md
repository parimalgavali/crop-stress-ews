# Week 38: GRU-D input-decay fix (US-52)

Review finding 4.1: input-decay weights were stuck at zero-init (dead gradients). Fixed with
positive init + regression tests; scores to be recomputed in the corrective release.
