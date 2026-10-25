import { GoldQuestion } from "./evaluationData";

export const GOLD_QUESTIONS: GoldQuestion[] = [
  {
    "question_id": "gold_q01_single_vaswani",
    "paper_ids": [
      "1706.03762_Attention_Is_All_You_Need"
    ],
    "question": "What mathematical scaling factor is used in Scaled Dot-Product Attention in the Transformer and why is it applied?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "The scaling factor is 1/sqrt(d_k), where d_k is the key dimension. It is applied to prevent dot products from growing excessively large for large values of d_k, which would push the softmax function into regions with extremely small gradients."
    ],
    "gold_evidence": [
      {
        "paper_id": "1706.03762_Attention_Is_All_You_Need",
        "chunk_id": "chunk_03",
        "page": 3,
        "section": "3.2.1 Scaled Dot-Product Attention",
        "quote": "We compute the dot products of the query with all keys, divide each by sqrt(d_k), and apply a softmax function to obtain the weights on the values. To counteract this effect, we scale the dot products by 1/sqrt(d_k)."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "transformer",
          "scaled_dot"
        ],
        "edges": [
          {
            "source": "transformer",
            "target": "scaled_dot",
            "type": "USES_ATTENTION",
            "paper_id": "1706.03762_Attention_Is_All_You_Need",
            "chunk_id": "chunk_03"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 3.2.1 Scaled Dot-Product Attention."
    }
  },
  {
    "question_id": "gold_q02_single_gcn_trick",
    "paper_ids": [
      "1609.02907_GCN"
    ],
    "question": "What is the renormalization trick introduced in Graph Convolutional Networks (GCN) to address exploding or vanishing gradients?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "The renormalization trick replaces (I_N + D^(-1/2) A D^(-1/2)) with D_tilde^(-1/2) A_tilde D_tilde^(-1/2), where A_tilde = A + I_N and D_tilde_ii = sum_j A_tilde_ij, adding self-loops and symmetrically normalizing the adjacency matrix to constrain eigenvalues in deep architectures."
    ],
    "gold_evidence": [
      {
        "paper_id": "1609.02907_GCN",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "2 Spectral Graph Convolutions",
        "quote": "We introduce the following renormalization trick: I_N + D^(-1/2) A D^(-1/2) -> D_tilde^(-1/2) A_tilde D_tilde^(-1/2) with A_tilde = A + I_N and D_tilde_ii = sum_j A_tilde_ij."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "gcn_model",
          "renormalization_trick"
        ],
        "edges": [
          {
            "source": "gcn_model",
            "target": "renormalization_trick",
            "type": "NORMALIZES_ADJACENCY",
            "paper_id": "1609.02907_GCN",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 2 Spectral Graph Convolutions."
    }
  },
  {
    "question_id": "gold_q03_single_gat_alpha",
    "paper_ids": [
      "1710.10903_GAT"
    ],
    "question": "How do attention coefficients alpha_ij in Graph Attention Networks (GAT) weight neighbor node features?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "Attention coefficients alpha_ij are computed using a shared attentional mechanism parameterized by weight vector a, followed by LeakyReLU non-linearity and softmax normalization across all neighbors j in N_i: alpha_ij = softmax_j(LeakyReLU(a^T [Wh_i || Wh_j]))."
    ],
    "gold_evidence": [
      {
        "paper_id": "1710.10903_GAT",
        "chunk_id": "chunk_02",
        "page": 2,
        "section": "2.1 Graph Attentional Layer",
        "quote": "To make coefficients easily comparable across different nodes, we normalize them across all choices of j using the softmax function: alpha_ij = exp(LeakyReLU(a^T [Wh_i || Wh_j])) / sum_{k in N_i} exp(LeakyReLU(a^T [Wh_i || Wh_k]))."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "gat_layer",
          "attention_coefficients"
        ],
        "edges": [
          {
            "source": "gat_layer",
            "target": "attention_coefficients",
            "type": "COMPUTES_SOFTMAX_COEFFICIENTS",
            "paper_id": "1710.10903_GAT",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 2.1 Graph Attentional Layer."
    }
  },
  {
    "question_id": "gold_q04_single_graphsage_agg",
    "paper_ids": [
      "1706.02216_GraphSAGE"
    ],
    "question": "What candidate aggregator architectures were evaluated in GraphSAGE for neighbor feature aggregation?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "GraphSAGE evaluated Mean aggregator, LSTM aggregator (applied to randomly permuted neighbor sequences), and Pooling aggregator (symmetric max-pooling over element-wise feedforward transformations of neighbor representations)."
    ],
    "gold_evidence": [
      {
        "paper_id": "1706.02216_GraphSAGE",
        "chunk_id": "chunk_03",
        "page": 4,
        "section": "3.3 Aggregator Architectures",
        "quote": "We examine three candidate aggregator functions: Mean aggregator, LSTM aggregator, and Pooling aggregator."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "graphsage_framework",
          "aggregator_architectures"
        ],
        "edges": [
          {
            "source": "graphsage_framework",
            "target": "aggregator_architectures",
            "type": "EVALUATES_NEIGHBOR_AGGREGATORS",
            "paper_id": "1706.02216_GraphSAGE",
            "chunk_id": "chunk_03"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 3.3 Aggregator Architectures."
    }
  },
  {
    "question_id": "gold_q05_single_rag_models",
    "paper_ids": [
      "2005.11401_RAG"
    ],
    "question": "What two distinct formulations of retrieval-augmented generation models were introduced in the RAG paper?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "The two formulations are RAG-Sequence (which conditions the entire output sequence generation on the same retrieved passage) and RAG-Token (which can marginalize over different retrieved passages at each output token position)."
    ],
    "gold_evidence": [
      {
        "paper_id": "2005.11401_RAG",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "2.1 Models",
        "quote": "We propose two models: RAG-Sequence, which uses the same retrieved passage to generate the complete sequence, and RAG-Token, which can use different passages to generate each token."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "rag_architecture",
          "sequence_and_token_formulations"
        ],
        "edges": [
          {
            "source": "rag_architecture",
            "target": "sequence_and_token_formulations",
            "type": "INTRODUCES_FORMULATIONS",
            "paper_id": "2005.11401_RAG",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 2.1 Models."
    }
  },
  {
    "question_id": "gold_q06_single_deepwalk_hierarchical",
    "paper_ids": [
      "1403.6652_DeepWalk"
    ],
    "question": "How does DeepWalk accelerate language model optimization over network vertex random walks?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "DeepWalk utilizes Hierarchical Softmax based on Huffman trees to reduce the computational complexity of computing conditional probability distributions over network vertices from O(|V|) to O(log |V|)."
    ],
    "gold_evidence": [
      {
        "paper_id": "1403.6652_DeepWalk",
        "chunk_id": "chunk_02",
        "page": 4,
        "section": "3.2 Hierarchical Softmax",
        "quote": "To solve this problem, we use Hierarchical Softmax to approximate the probability distribution. By assigning vertices to the leaves of a binary tree, the prediction problem turns into maximizing the probability of the path to the leaf, reducing complexity from O(|V|) to O(log |V|)."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "deepwalk_random_walks",
          "hierarchical_softmax"
        ],
        "edges": [
          {
            "source": "deepwalk_random_walks",
            "target": "hierarchical_softmax",
            "type": "REDUCES_COMPLEXITY_VIA_TREE",
            "paper_id": "1403.6652_DeepWalk",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 3.2 Hierarchical Softmax."
    }
  },
  {
    "question_id": "gold_q07_single_node2vec_search_biases",
    "paper_ids": [
      "1607.00653_node2vec"
    ],
    "question": "What do hyperparameters p and q govern in the node2vec second-order random walk procedure?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "Parameter p (return parameter) controls the likelihood of immediately revisiting the node just traversed, while parameter q (in-out parameter) governs the search bias between exploring local micro-structures (BFS-like) versus outward macro-structures (DFS-like)."
    ],
    "gold_evidence": [
      {
        "paper_id": "1607.00653_node2vec",
        "chunk_id": "chunk_02",
        "page": 4,
        "section": "3.2.2 Search bias alpha",
        "quote": "Parameter p controls the likelihood of immediately revisiting the node in the walk, while parameter q allows the search to differentiate between inward and outward nodes."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "node2vec_random_walk",
          "return_inout_parameters"
        ],
        "edges": [
          {
            "source": "node2vec_random_walk",
            "target": "return_inout_parameters",
            "type": "GOVERNS_INTERPOLATION_BFS_DFS",
            "paper_id": "1607.00653_node2vec",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 3.2.2 Search bias alpha."
    }
  },
  {
    "question_id": "gold_q08_single_bert_pretraining_tasks",
    "paper_ids": [
      "1810.04805_BERT"
    ],
    "question": "What two self-supervised pre-training objectives are jointly optimized in BERT?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "BERT is trained simultaneously on Masked Language Modeling (MLM), where 15% of input tokens are masked and predicted, and Next Sentence Prediction (NSP), a binarized task predicting whether sentence B follows sentence A in the corpus."
    ],
    "gold_evidence": [
      {
        "paper_id": "1810.04805_BERT",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "3.1 Pre-training BERT",
        "quote": "We argue that current techniques restrict the power of the pre-trained representations. We pre-train BERT using two unsupervised tasks: Masked LM (Task #1) and Next Sentence Prediction (Task #2)."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "bert_bidirectional",
          "masked_lm_and_nsp"
        ],
        "edges": [
          {
            "source": "bert_bidirectional",
            "target": "masked_lm_and_nsp",
            "type": "TRAINED_ON_DUAL_OBJECTIVES",
            "paper_id": "1810.04805_BERT",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 3.1 Pre-training BERT."
    }
  },
  {
    "question_id": "gold_q09_single_cot_fewshot",
    "paper_ids": [
      "2201.11903_Chain_of_Thought"
    ],
    "question": "How is Chain-of-Thought (CoT) prompting implemented without modifying language model parameters?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "CoT prompting is implemented entirely through in-context few-shot exemplars that demonstrate step-by-step intermediate natural language reasoning chains before reaching the final answer."
    ],
    "gold_evidence": [
      {
        "paper_id": "2201.11903_Chain_of_Thought",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "Chain-of-thought prompting is an approach where few-shot exemplars are composed of triples: <input, chain of thought, output>. The chain of thought is a series of intermediate natural language reasoning steps that lead to the final output."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "chain_of_thought_prompting",
          "in_context_exemplars"
        ],
        "edges": [
          {
            "source": "chain_of_thought_prompting",
            "target": "in_context_exemplars",
            "type": "ELICITS_STEP_BY_STEP_REASONING",
            "paper_id": "2201.11903_Chain_of_Thought",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 1 Introduction."
    }
  },
  {
    "question_id": "gold_q10_single_kg_embedding_transe",
    "paper_ids": [
      "1703.08098_KG_Embedding_Survey"
    ],
    "question": "What geometric formulation does TransE assume between head, relation, and tail embeddings?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "TransE models relations as translational distance vectors in continuous vector space, enforcing the score function f_r(h, t) = -||h + r - t||_{1/2} such that head vector plus relation vector approximates tail vector (h + r approx t)."
    ],
    "gold_evidence": [
      {
        "paper_id": "1703.08098_KG_Embedding_Survey",
        "chunk_id": "chunk_02",
        "page": 4,
        "section": "3.1 Translational Distance Models",
        "quote": "TransE models relations as translations in the embedding space: if (h, r, t) holds, then the embedding of the tail entity t should be close to the embedding of the head entity h plus some relation vector r, i.e., h + r approx t."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "knowledge_graph_embeddings",
          "transe_translational_model"
        ],
        "edges": [
          {
            "source": "knowledge_graph_embeddings",
            "target": "transe_translational_model",
            "type": "MODELS_RELATION_AS_VECTOR_TRANSLATION",
            "paper_id": "1703.08098_KG_Embedding_Survey",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 3.1 Translational Distance Models."
    }
  },
  {
    "question_id": "gold_q11_single_lora_rank_decomposition",
    "paper_ids": [
      "2106.09685_LoRA"
    ],
    "question": "How does Low-Rank Adaptation (LoRA) decompose weight updates during fine-tuning?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "LoRA decomposes parameter updates into low-rank matrices delta W = B * A, where B in R^(d x r) and A in R^(r x k) with intrinsic rank r << min(d, k), freezing pre-trained weights W_0 while training only A and B."
    ],
    "gold_evidence": [
      {
        "paper_id": "2106.09685_LoRA",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "4 Problem Statement & Methods",
        "quote": "We propose Low-Rank Adaptation (LoRA), which decomposes the weight update matrix delta W into the product of two low-rank matrices: delta W = B * A, where B is initialized to 0 and A is initialized from a Gaussian distribution."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "lora_low_rank_adaptation",
          "low_rank_decomposition_matrices"
        ],
        "edges": [
          {
            "source": "lora_low_rank_adaptation",
            "target": "low_rank_decomposition_matrices",
            "type": "CONSTRAINS_UPDATES_TO_LOW_RANK",
            "paper_id": "2106.09685_LoRA",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 4 Problem Statement & Methods."
    }
  },
  {
    "question_id": "gold_q12_single_roberta_design_modifications",
    "paper_ids": [
      "1907.11692_RoBERTa"
    ],
    "question": "What four key design modifications did RoBERTa introduce to improve BERT pre-training?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "RoBERTa trained longer with larger batch sizes and more data, removed the Next Sentence Prediction (NSP) objective, trained on longer sequences, and dynamically changed the masking pattern applied to the training data."
    ],
    "gold_evidence": [
      {
        "paper_id": "1907.11692_RoBERTa",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "Our modifications are simple: (1) training the model longer, with bigger batches, over more data; (2) removing the next sentence prediction objective; (3) training on longer sequences; and (4) dynamically changing the masking pattern applied to the training data."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "roberta_model",
          "roberta_modifications"
        ],
        "edges": [
          {
            "source": "roberta_model",
            "target": "roberta_modifications",
            "type": "OPTIMIZES_TRAINING_RECIPE",
            "paper_id": "1907.11692_RoBERTa",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 1 Introduction."
    }
  },
  {
    "question_id": "gold_q13_single_flashattention_io_awareness",
    "paper_ids": [
      "2205.14135_FlashAttention"
    ],
    "question": "How does FlashAttention achieve IO-awareness across GPU memory hierarchies?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "FlashAttention tiles input matrices into blocks loaded from high-bandwidth HBM into fast on-chip SRAM, computing softmax normalization incrementally via online softmax without materializing the full N x N attention matrix to HBM."
    ],
    "gold_evidence": [
      {
        "paper_id": "2205.14135_FlashAttention",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "FlashAttention computes exact attention with fewer memory accesses by tiling: it loads blocks of Q, K, V from slow GPU HBM into fast SRAM, computes attention with respect to that block, and updates the output in SRAM incrementally using online softmax."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "flashattention_tiling",
          "io_aware_memory_hierarchy"
        ],
        "edges": [
          {
            "source": "flashattention_tiling",
            "target": "io_aware_memory_hierarchy",
            "type": "REDUCES_HBM_READ_WRITES",
            "paper_id": "2205.14135_FlashAttention",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 1 Introduction."
    }
  },
  {
    "question_id": "gold_q14_single_gin_weisfeiler_lehman",
    "paper_ids": [
      "1810.00826_GIN"
    ],
    "question": "What theoretical upper bound on graph neural network expressiveness was established in the GIN paper?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "The GIN paper proved that message-passing Graph Neural Networks are at most as powerful as the 1-dimensional Weisfeiler-Lehman (1-WL) graph isomorphism test in distinguishing non-isomorphic graph structures."
    ],
    "gold_evidence": [
      {
        "paper_id": "1810.00826_GIN",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "We prove that message-passing GNNs are at most as powerful as the 1-WL test in distinguishing non-isomorphic graphs. We then formulate Graph Isomorphism Network (GIN) whose representational power equals the 1-WL test."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "gin_isomorphism_network",
          "weisfeiler_lehman_test"
        ],
        "edges": [
          {
            "source": "gin_isomorphism_network",
            "target": "weisfeiler_lehman_test",
            "type": "BOUNDS_EXPRESSIVE_POWER",
            "paper_id": "1810.00826_GIN",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 1 Introduction."
    }
  },
  {
    "question_id": "gold_q15_single_ddpm_reparameterization",
    "paper_ids": [
      "2006.11239_DDPM"
    ],
    "question": "What simplified objective does DDPM use to train the reverse diffusion process?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "DDPM trains a neural network to predict the added Gaussian noise epsilon at timestep t using a mean squared error loss L_simple = E_{t, x_0, epsilon}[ ||epsilon - epsilon_theta(sqrt(alpha_bar_t) x_0 + sqrt(1 - alpha_bar_t) epsilon, t)||^2 ]."
    ],
    "gold_evidence": [
      {
        "paper_id": "2006.11239_DDPM",
        "chunk_id": "chunk_02",
        "page": 4,
        "section": "3.4 Simplified Training Objective",
        "quote": "We find that training our model on the following simplified objective is beneficial to sample quality: L_simple(theta) = E_{t, x_0, epsilon}[ ||epsilon - epsilon_theta(sqrt(alpha_bar_t) x_0 + sqrt(1 - alpha_bar_t) epsilon, t)||^2 ]."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "ddpm_diffusion_model",
          "simplified_noise_prediction_loss"
        ],
        "edges": [
          {
            "source": "ddpm_diffusion_model",
            "target": "simplified_noise_prediction_loss",
            "type": "TRAINS_ON_MSE_NOISE",
            "paper_id": "2006.11239_DDPM",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 3.4 Simplified Training Objective."
    }
  },
  {
    "question_id": "gold_q16_single_clip_contrastive_loss",
    "paper_ids": [
      "2103.00020_CLIP"
    ],
    "question": "How does CLIP jointly train its image and text encoders?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "CLIP uses a symmetric cross-entropy contrastive loss over cosine similarities of batch embeddings, maximizing diagonal cosine similarities of matching (image, text) pairs while minimizing off-diagonal cosine similarities of non-matching pairs."
    ],
    "gold_evidence": [
      {
        "paper_id": "2103.00020_CLIP",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "2.2 Approach",
        "quote": "Given a batch of N (image, text) pairs, CLIP is trained to predict which of the N x N possible pairings across a batch actually occurred by optimizing a symmetric cross-entropy loss over the planned cosine similarities."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "clip_multimodal",
          "contrastive_symmetric_cross_entropy"
        ],
        "edges": [
          {
            "source": "clip_multimodal",
            "target": "contrastive_symmetric_cross_entropy",
            "type": "MAXIMIZES_PAIR_SIMILARITY",
            "paper_id": "2103.00020_CLIP",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 2.2 Approach."
    }
  },
  {
    "question_id": "gold_q17_single_react_synergy",
    "paper_ids": [
      "2210.03629_ReAct"
    ],
    "question": "How does ReAct combine reasoning traces with external environment actions?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "ReAct interleaves reasoning thought traces (which help plan, track progress, and handle exceptions) with external actions (such as searching or looking up Wikipedia), receiving environmental observations before generating the next thought."
    ],
    "gold_evidence": [
      {
        "paper_id": "2210.03629_ReAct",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "ReAct prompts LLMs to generate reasoning traces and task-specific actions in an interleaved manner: thoughts help update action plans and adjust tracking, while actions execute tools and return observations from external sources."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "react_reasoning_and_acting",
          "interleaved_thought_action_observation"
        ],
        "edges": [
          {
            "source": "react_reasoning_and_acting",
            "target": "interleaved_thought_action_observation",
            "type": "SYNERGIZES_REASONING_WITH_TOOLS",
            "paper_id": "2210.03629_ReAct",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 1 Introduction."
    }
  },
  {
    "question_id": "gold_q18_single_dpo_closed_form",
    "paper_ids": [
      "2305.18290_DPO"
    ],
    "question": "How does Direct Preference Optimization (DPO) bypass training a separate reward model in RLHF?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "DPO derives an exact closed-form expression for the optimal policy under the Bradley-Terry preference model, enabling direct optimization of the language model policy using a binary cross-entropy objective over preferred versus dispreferred completions."
    ],
    "gold_evidence": [
      {
        "paper_id": "2305.18290_DPO",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "DPO implicitly optimizes the same objective as RLHF (maximizing reward while constraining KL divergence) but directly uses a simple cross-entropy loss on preference data, completely eliminating the need to train a separate reward model or sample from the policy during training."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "direct_preference_optimization",
          "closed_form_preference_loss"
        ],
        "edges": [
          {
            "source": "direct_preference_optimization",
            "target": "closed_form_preference_loss",
            "type": "ELIMINATES_REWARD_MODEL_FITTING",
            "paper_id": "2305.18290_DPO",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 1 Introduction."
    }
  },
  {
    "question_id": "gold_q19_single_dpr_dual_encoders",
    "paper_ids": [
      "2004.04906_DPR"
    ],
    "question": "Why does DPR train independent encoders for questions and passages instead of a single joint model?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "DPR uses separate question and passage encoders E_Q and E_P to allow all corpus passages to be indexed offline into a vector database (e.g. FAISS), so at query time only the question must be encoded before executing fast maximum inner product search."
    ],
    "gold_evidence": [
      {
        "paper_id": "2004.04906_DPR",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "2 Dense Passage Retriever (DPR)",
        "quote": "DPR uses two independent BERT encoders: one for passages and one for questions. This allows all passages in the corpus to be indexed offline beforehand; at run-time, we only need to encode the question and perform maximum inner product search."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "dense_passage_retriever",
          "dual_independent_encoders"
        ],
        "edges": [
          {
            "source": "dense_passage_retriever",
            "target": "dual_independent_encoders",
            "type": "ENABLES_OFFLINE_CORPUS_INDEXING",
            "paper_id": "2004.04906_DPR",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 2 Dense Passage Retriever (DPR)."
    }
  },
  {
    "question_id": "gold_q20_single_mecch_metapath_convolutions",
    "paper_ids": [
      "2211.12792_MECCH"
    ],
    "question": "How does MECCH preserve heterogeneous graph semantics across different edge relation types?",
    "category": "single_paper",
    "answerable": true,
    "gold_answers": [
      "MECCH decomposes heterogeneous networks into metapath contexts, using metapath context convolutions and hierarchical attention to aggregate topological context across diverse entity and relation types without semantic loss."
    ],
    "gold_evidence": [
      {
        "paper_id": "2211.12792_MECCH",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "MECCH extracts structural metapath contexts and applies metapath context convolutions, followed by semantic-level attention to dynamically fuse representations across different metapaths."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "mecch_heterogeneous_gnn",
          "metapath_context_convolutions"
        ],
        "edges": [
          {
            "source": "mecch_heterogeneous_gnn",
            "target": "metapath_context_convolutions",
            "type": "FUSES_HETEROGENEOUS_SEMANTICS",
            "paper_id": "2211.12792_MECCH",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 1,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated single-hop fact from 1 Introduction."
    }
  },
  {
    "question_id": "gold_q21_multihop_single_vaswani_multihead",
    "paper_ids": [
      "1706.03762_Attention_Is_All_You_Need"
    ],
    "question": "How does the Transformer project queries, keys, and values through parameter matrices before computing scaled dot-product attention and concatenating heads?",
    "category": "multi_hop_single_paper",
    "answerable": true,
    "gold_answers": [
      "The Transformer linearly projects queries, keys, and values h times with learned parameter matrices W_i^Q, W_i^K, and W_i^V to dimensions d_k, d_k, and d_v. It then computes scaled dot-product attention in parallel across all h heads, concatenates the resulting head representations, and projects them once more using matrix W^O to produce the final layer output."
    ],
    "gold_evidence": [
      {
        "paper_id": "1706.03762_Attention_Is_All_You_Need",
        "chunk_id": "chunk_03",
        "page": 2,
        "section": "Section 2 / Methods",
        "quote": "Multi-head attention allows the model to jointly attend to information from different representation subspaces at different positions."
      },
      {
        "paper_id": "1706.03762_Attention_Is_All_You_Need",
        "chunk_id": "chunk_04",
        "page": 3,
        "section": "Section 3 / Analysis",
        "quote": "MultiHead(Q, K, V) = Concat(head_1, ..., head_h) W^O where head_i = Attention(Q W_i^Q, K W_i^K, V W_i^V)."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "linear_projections_qkv",
          "parallel_attention_heads",
          "concatenation_and_wo_projection"
        ],
        "edges": [
          {
            "source": "linear_projections_qkv",
            "target": "parallel_attention_heads",
            "type": "FEEDS_PARALLEL_HEADS",
            "paper_id": "1706.03762_Attention_Is_All_You_Need",
            "chunk_id": "chunk_03"
          },
          {
            "source": "parallel_attention_heads",
            "target": "concatenation_and_wo_projection",
            "type": "CONCATENATED_AND_PROJECTED",
            "paper_id": "1706.03762_Attention_Is_All_You_Need",
            "chunk_id": "chunk_04"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Multi-hop single-paper reasoning chain (2 hops) across 1706.03762_Attention_Is_All_You_Need."
    }
  },
  {
    "question_id": "gold_q22_multihop_single_gcn_first_order",
    "paper_ids": [
      "1609.02907_GCN"
    ],
    "question": "Trace the mathematical transition in GCN from ChebNet Chebyshev polynomial truncation to the final simplified first-order graph convolutional layer.",
    "category": "multi_hop_single_paper",
    "answerable": true,
    "gold_answers": [
      "GCN begins from Hammond's spectral graph formulation and truncates Chebyshev polynomials to order K=1 with lambda_max approx 2, obtaining theta_0 x + theta_1 (L - I) x. It then constrains parameters theta = theta_0 = -theta_1 to prevent overfitting, yielding theta (I + D^(-1/2) A D^(-1/2)) x, and finally applies the renormalization trick to form D_tilde^(-1/2) A_tilde D_tilde^(-1/2) X W."
    ],
    "gold_evidence": [
      {
        "paper_id": "1609.02907_GCN",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "Section 2 / Methods",
        "quote": "A spectral convolution on graphs is defined as the multiplication of a signal x with a filter parameterized by Chebyshev polynomials."
      },
      {
        "paper_id": "1609.02907_GCN",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "Section 3 / Analysis",
        "quote": "We approximate lambda_max approx 2 and constrain theta_0 = -theta_1 to arrive at our localized first-order formulation."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "chebyshev_polynomial_truncation",
          "parameter_constraint_theta",
          "renormalized_gcn_layer"
        ],
        "edges": [
          {
            "source": "chebyshev_polynomial_truncation",
            "target": "parameter_constraint_theta",
            "type": "SIMPLIFIES_COEFFICIENTS",
            "paper_id": "1609.02907_GCN",
            "chunk_id": "chunk_01"
          },
          {
            "source": "parameter_constraint_theta",
            "target": "renormalized_gcn_layer",
            "type": "APPLIES_RENORMALIZATION_TRICK",
            "paper_id": "1609.02907_GCN",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Multi-hop single-paper reasoning chain (2 hops) across 1609.02907_GCN."
    }
  },
  {
    "question_id": "gold_q23_multihop_single_gat_multihead",
    "paper_ids": [
      "1710.10903_GAT"
    ],
    "question": "How does GAT transition from multi-head concatenation in intermediate hidden layers to multi-head averaging in the final output prediction layer?",
    "category": "multi_hop_single_paper",
    "answerable": true,
    "gold_answers": [
      "In intermediate layers, GAT concatenates the features produced by K independent attention heads (h_i' = ||_{k=1}^K sigma(sum_j alpha_ij^k W^k h_j)) to enrich representation capacity; in the final output prediction layer, concatenation is replaced by arithmetic averaging (h_i' = sigma(1/K sum_{k=1}^K sum_j alpha_ij^k W^k h_j)) before softmax classification."
    ],
    "gold_evidence": [
      {
        "paper_id": "1710.10903_GAT",
        "chunk_id": "chunk_02",
        "page": 2,
        "section": "Section 2 / Methods",
        "quote": "To stabilize the learning process of self-attention, we employ multi-head attention: K independent attention mechanisms execute the transformation."
      },
      {
        "paper_id": "1710.10903_GAT",
        "chunk_id": "chunk_03",
        "page": 3,
        "section": "Section 3 / Analysis",
        "quote": "For the final classification layer, concatenation is no longer sensible\u2014instead, we employ averaging and delay applying the final non-linearity."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "multihead_attention_layer",
          "concatenation_intermediate_features",
          "averaging_final_classification"
        ],
        "edges": [
          {
            "source": "multihead_attention_layer",
            "target": "concatenation_intermediate_features",
            "type": "CONCATENATES_K_HEADS",
            "paper_id": "1710.10903_GAT",
            "chunk_id": "chunk_02"
          },
          {
            "source": "concatenation_intermediate_features",
            "target": "averaging_final_classification",
            "type": "SWITCHES_TO_AVERAGING_AT_OUTPUT",
            "paper_id": "1710.10903_GAT",
            "chunk_id": "chunk_03"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Multi-hop single-paper reasoning chain (2 hops) across 1710.10903_GAT."
    }
  },
  {
    "question_id": "gold_q24_multihop_single_graphsage_k_hop",
    "paper_ids": [
      "1706.02216_GraphSAGE"
    ],
    "question": "Explain how GraphSAGE propagates and aggregates representations iteratively from depth k=1 to depth K across sampled neighborhoods.",
    "category": "multi_hop_single_paper",
    "answerable": true,
    "gold_answers": [
      "GraphSAGE begins at depth k=0 by initializing node representations with input features. For each depth k=1..K, each node aggregates representations of its sampled neighbors using an aggregator function, concatenates the resulting neighborhood vector with its own current representation, and multiplies by weight matrix W^k with a non-linearity before normalizing representations to unit L2 norm."
    ],
    "gold_evidence": [
      {
        "paper_id": "1706.02216_GraphSAGE",
        "chunk_id": "chunk_02",
        "page": 2,
        "section": "Section 2 / Methods",
        "quote": "Algorithm 1 describes the GraphSAGE embedding generation algorithm. In each iteration k, nodes aggregate representations of their immediate neighbors."
      },
      {
        "paper_id": "1706.02216_GraphSAGE",
        "chunk_id": "chunk_03",
        "page": 3,
        "section": "Section 3 / Analysis",
        "quote": "h_{N(v)}^k <- AGGREGATE_k({h_u^{k-1}, forall u in N(v)}); h_v^k <- sigma(W^k * [h_v^{k-1} || h_{N(v)}^k])."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "input_feature_initialization",
          "sampled_neighborhood_aggregation",
          "concatenation_weight_transformation"
        ],
        "edges": [
          {
            "source": "input_feature_initialization",
            "target": "sampled_neighborhood_aggregation",
            "type": "AGGREGATES_SAMPLED_NEIGHBORS",
            "paper_id": "1706.02216_GraphSAGE",
            "chunk_id": "chunk_02"
          },
          {
            "source": "sampled_neighborhood_aggregation",
            "target": "concatenation_weight_transformation",
            "type": "CONCATENATES_WITH_SELF_AND_PROJECTS",
            "paper_id": "1706.02216_GraphSAGE",
            "chunk_id": "chunk_03"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Multi-hop single-paper reasoning chain (2 hops) across 1706.02216_GraphSAGE."
    }
  },
  {
    "question_id": "gold_q25_multihop_single_rag_sequence_marginalization",
    "paper_ids": [
      "2005.11401_RAG"
    ],
    "question": "How does RAG-Sequence compute document marginalization probabilities across top-K retrieved passages during beam search?",
    "category": "multi_hop_single_paper",
    "answerable": true,
    "gold_answers": [
      "RAG-Sequence retrieves top-K candidate passages using DPR, generates candidate target sequences independently for each passage using beam search, scores each candidate hypothesis by multiplying the passage prior probability p(z|x) by sequence likelihood p(y|x, z), and sums across passages that generated the same candidate sequence."
    ],
    "gold_evidence": [
      {
        "paper_id": "2005.11401_RAG",
        "chunk_id": "chunk_02",
        "page": 2,
        "section": "Section 2 / Methods",
        "quote": "For RAG-Sequence, the top K documents are retrieved using the retriever, and the generator produces an output sequence for each document."
      },
      {
        "paper_id": "2005.11401_RAG",
        "chunk_id": "chunk_03",
        "page": 3,
        "section": "Section 3 / Analysis",
        "quote": "The probability of the sequence is marginalized across all K documents: p(y|x) = sum_{z in top-K} p(z|x) prod_i p(y_i|x, z, y_{1:i-1})."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "dpr_retrieval_prior",
          "per_passage_beam_generation",
          "sequence_level_marginalization"
        ],
        "edges": [
          {
            "source": "dpr_retrieval_prior",
            "target": "per_passage_beam_generation",
            "type": "CONDITIONS_GENERATOR_ON_PASSAGE",
            "paper_id": "2005.11401_RAG",
            "chunk_id": "chunk_02"
          },
          {
            "source": "per_passage_beam_generation",
            "target": "sequence_level_marginalization",
            "type": "MARGINALIZES_PROBABILITIES_OVER_TOP_K",
            "paper_id": "2005.11401_RAG",
            "chunk_id": "chunk_03"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Multi-hop single-paper reasoning chain (2 hops) across 2005.11401_RAG."
    }
  },
  {
    "question_id": "gold_q26_multihop_single_deepwalk_streaming",
    "paper_ids": [
      "1403.6652_DeepWalk"
    ],
    "question": "How does DeepWalk integrate truncated random walks with the SkipGram architecture to construct continuous vertex representations?",
    "category": "multi_hop_single_paper",
    "answerable": true,
    "gold_answers": [
      "DeepWalk generates uniform random walks of fixed length t starting from each vertex v_i in graph G, treating each walk as a sentence of discrete tokens. It then passes these walk sequences through the SkipGram algorithm, which slides a context window of size w to maximize the log probability of observing neighbor vertices within the window using hierarchical softmax."
    ],
    "gold_evidence": [
      {
        "paper_id": "1403.6652_DeepWalk",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "Section 2 / Methods",
        "quote": "We present DeepWalk, an approach for learning latent representations of vertices in a network using local information obtained from truncated random walks."
      },
      {
        "paper_id": "1403.6652_DeepWalk",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "Section 3 / Analysis",
        "quote": "The walk sequences are fed into the SkipGram algorithm, maximizing the co-occurrence probability of vertices within window w."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "truncated_random_walk_generator",
          "walk_as_sentence_corpus",
          "skipgram_hierarchical_softmax"
        ],
        "edges": [
          {
            "source": "truncated_random_walk_generator",
            "target": "walk_as_sentence_corpus",
            "type": "CONVERTS_GRAPH_TOPOLOGY_TO_STRINGS",
            "paper_id": "1403.6652_DeepWalk",
            "chunk_id": "chunk_01"
          },
          {
            "source": "walk_as_sentence_corpus",
            "target": "skipgram_hierarchical_softmax",
            "type": "OPTIMIZES_CO_OCCURRENCE_LIKELIHOOD",
            "paper_id": "1403.6652_DeepWalk",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Multi-hop single-paper reasoning chain (2 hops) across 1403.6652_DeepWalk."
    }
  },
  {
    "question_id": "gold_q27_multihop_single_node2vec_second_order",
    "paper_ids": [
      "1607.00653_node2vec"
    ],
    "question": "How does node2vec determine transition probabilities using previous node t, current node v, and candidate destination node x?",
    "category": "multi_hop_single_paper",
    "answerable": true,
    "gold_answers": [
      "node2vec evaluates the shortest path distance d_{tx} between previous node t and candidate node x: if d_{tx}=0, transition bias is set to 1/p; if d_{tx}=1, transition bias is set to 1; and if d_{tx}=2, transition bias is set to 1/q. These unnormalized biases are multiplied by edge weight w_{vx} and normalized across all neighbors of v to sample the next step."
    ],
    "gold_evidence": [
      {
        "paper_id": "1607.00653_node2vec",
        "chunk_id": "chunk_02",
        "page": 2,
        "section": "Section 2 / Methods",
        "quote": "The transition probability pi_{vx} is set to alpha_{pq}(t, x) * w_{vx}, where alpha_{pq}(t, x) depends on the shortest path distance d_{tx}."
      },
      {
        "paper_id": "1607.00653_node2vec",
        "chunk_id": "chunk_03",
        "page": 3,
        "section": "Section 3 / Analysis",
        "quote": "alpha_{pq}(t, x) = 1/p if d_{tx}=0; 1 if d_{tx}=1; 1/q if d_{tx}=2."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "previous_node_context",
          "shortest_path_distance_evaluation",
          "second_order_transition_sampling"
        ],
        "edges": [
          {
            "source": "previous_node_context",
            "target": "shortest_path_distance_evaluation",
            "type": "EVALUATES_DISTANCE_TO_PREVIOUS",
            "paper_id": "1607.00653_node2vec",
            "chunk_id": "chunk_02"
          },
          {
            "source": "shortest_path_distance_evaluation",
            "target": "second_order_transition_sampling",
            "type": "SCALES_PROBABILITY_BY_P_Q",
            "paper_id": "1607.00653_node2vec",
            "chunk_id": "chunk_03"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Multi-hop single-paper reasoning chain (2 hops) across 1607.00653_node2vec."
    }
  },
  {
    "question_id": "gold_q28_multihop_single_bert_input_representation",
    "paper_ids": [
      "1810.04805_BERT"
    ],
    "question": "How does BERT construct the input representation for each token from three distinct embedding lookups?",
    "category": "multi_hop_single_paper",
    "answerable": true,
    "gold_answers": [
      "For each token in the sequence, BERT performs three independent vector lookups: WordPiece Token Embeddings, Segment Embeddings (differentiating sentence A from sentence B), and learned Position Embeddings (encoding token index). It then sums these three embedding vectors element-wise to form the initial hidden state input to the transformer stack."
    ],
    "gold_evidence": [
      {
        "paper_id": "1810.04805_BERT",
        "chunk_id": "chunk_02",
        "page": 2,
        "section": "Section 2 / Methods",
        "quote": "The input representation for a given token is constructed by summing the corresponding token, segment, and position embeddings."
      },
      {
        "paper_id": "1810.04805_BERT",
        "chunk_id": "chunk_03",
        "page": 3,
        "section": "Section 3 / Analysis",
        "quote": "We use WordPiece embeddings with a 30,000 token vocabulary. The first token of every sequence is always a special classification token ([CLS])."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "three_embedding_lookups",
          "elementwise_vector_summation",
          "transformer_encoder_stack_input"
        ],
        "edges": [
          {
            "source": "three_embedding_lookups",
            "target": "elementwise_vector_summation",
            "type": "SUMS_TOKEN_SEGMENT_POSITION",
            "paper_id": "1810.04805_BERT",
            "chunk_id": "chunk_02"
          },
          {
            "source": "elementwise_vector_summation",
            "target": "transformer_encoder_stack_input",
            "type": "FEEDS_FIRST_BIDIRECTIONAL_LAYER",
            "paper_id": "1810.04805_BERT",
            "chunk_id": "chunk_03"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Multi-hop single-paper reasoning chain (2 hops) across 1810.04805_BERT."
    }
  },
  {
    "question_id": "gold_q29_multihop_single_cot_arithmetic_scaling",
    "paper_ids": [
      "2201.11903_Chain_of_Thought"
    ],
    "question": "How does model parameter scale interact with chain-of-thought prompting benefits across GSM8K and SVAMP arithmetic benchmarks?",
    "category": "multi_hop_single_paper",
    "answerable": true,
    "gold_answers": [
      "Chain-of-thought prompting is an emergent capability that provides negligible benefit or even degrades performance in small language models (<10B parameters); only when model scale reaches ~100B parameters (such as PaLM 540B or GPT-3 175B) does CoT dramatically boost reasoning accuracy on complex multi-step math benchmarks like GSM8K."
    ],
    "gold_evidence": [
      {
        "paper_id": "2201.11903_Chain_of_Thought",
        "chunk_id": "chunk_02",
        "page": 2,
        "section": "Section 2 / Methods",
        "quote": "Chain-of-thought prompting does not positively impact performance for small models and only yields performance gains when used with models of ~100B parameters or larger."
      },
      {
        "paper_id": "2201.11903_Chain_of_Thought",
        "chunk_id": "chunk_03",
        "page": 3,
        "section": "Section 3 / Analysis",
        "quote": "On GSM8K, performance improves substantially as model scale increases, showing emergent reasoning behavior."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "model_parameter_scale_threshold",
          "emergent_reasoning_capability",
          "gsm8k_accuracy_surge"
        ],
        "edges": [
          {
            "source": "model_parameter_scale_threshold",
            "target": "emergent_reasoning_capability",
            "type": "ENABLES_EMERGENT_REASONING",
            "paper_id": "2201.11903_Chain_of_Thought",
            "chunk_id": "chunk_02"
          },
          {
            "source": "emergent_reasoning_capability",
            "target": "gsm8k_accuracy_surge",
            "type": "DRASTICALLY_OUTPERFORMS_STANDARD_PROMPTING",
            "paper_id": "2201.11903_Chain_of_Thought",
            "chunk_id": "chunk_03"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Multi-hop single-paper reasoning chain (2 hops) across 2201.11903_Chain_of_Thought."
    }
  },
  {
    "question_id": "gold_q30_multihop_single_kg_embedding_rescal_to_transe",
    "paper_ids": [
      "1703.08098_KG_Embedding_Survey"
    ],
    "question": "How did translational distance models like TransE address the parameter explosion of bilinear tensor factorization models like RESCAL?",
    "category": "multi_hop_single_paper",
    "answerable": true,
    "gold_answers": [
      "RESCAL represents each relation as a full d x d matrix M_r, leading to O(d^2) parameters per relation and high vulnerability to overfitting; TransE solved this by constraining each relation to a rank-1 translation vector r in R^d with scoring ||h + r - t||, dramatically reducing parameters per relation from O(d^2) to O(d)."
    ],
    "gold_evidence": [
      {
        "paper_id": "1703.08098_KG_Embedding_Survey",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "Section 2 / Methods",
        "quote": "RESCAL associates each relation with a full matrix M_r in R^{d x d}, which incurs quadratic parameter costs O(d^2) per relation."
      },
      {
        "paper_id": "1703.08098_KG_Embedding_Survey",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "Section 3 / Analysis",
        "quote": "TransE overcomes this parameter bloat by representing relations as translational vectors in R^d, reducing parameters per relation to O(d)."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "rescal_bilinear_matrix",
          "parameter_reduction_objective",
          "transe_linear_translational_vectors"
        ],
        "edges": [
          {
            "source": "rescal_bilinear_matrix",
            "target": "parameter_reduction_objective",
            "type": "EXPOSES_QUADRATIC_OVERFITTING",
            "paper_id": "1703.08098_KG_Embedding_Survey",
            "chunk_id": "chunk_01"
          },
          {
            "source": "parameter_reduction_objective",
            "target": "transe_linear_translational_vectors",
            "type": "REDUCES_RELATION_COMPLEXITY_TO_OD",
            "paper_id": "1703.08098_KG_Embedding_Survey",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Multi-hop single-paper reasoning chain (2 hops) across 1703.08098_KG_Embedding_Survey."
    }
  },
  {
    "question_id": "gold_q31_multihop_single_lora_inference_latency",
    "paper_ids": [
      "2106.09685_LoRA"
    ],
    "question": "How does LoRA eliminate inference latency overhead when deployed into production serving environments?",
    "category": "multi_hop_single_paper",
    "answerable": true,
    "gold_answers": [
      "During deployment, the low-rank update matrix delta W = B * A is multiplied out and directly summed into the frozen base model weights W_new = W_0 + B * A. Because the merged weights have the exact same shape as the original weight matrix, the model incurs zero additional inference latency or FLOPs overhead compared to the original un-adapted model."
    ],
    "gold_evidence": [
      {
        "paper_id": "2106.09685_LoRA",
        "chunk_id": "chunk_02",
        "page": 2,
        "section": "Section 2 / Methods",
        "quote": "When deployed in production, we can explicitly compute and store W = W_0 + B * A and perform inference as usual."
      },
      {
        "paper_id": "2106.09685_LoRA",
        "chunk_id": "chunk_03",
        "page": 3,
        "section": "Section 3 / Analysis",
        "quote": "Since W and W_0 have the exact same dimensions, this introduces no additional latency or memory footprint during inference."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "low_rank_update_decomposition",
          "weight_merging_into_w0",
          "zero_overhead_inference_serving"
        ],
        "edges": [
          {
            "source": "low_rank_update_decomposition",
            "target": "weight_merging_into_w0",
            "type": "EXPLICITLY_ADDS_DELTA_W_TO_BASE",
            "paper_id": "2106.09685_LoRA",
            "chunk_id": "chunk_02"
          },
          {
            "source": "weight_merging_into_w0",
            "target": "zero_overhead_inference_serving",
            "type": "ELIMINATES_RUNTIME_LATENCY_OVERHEAD",
            "paper_id": "2106.09685_LoRA",
            "chunk_id": "chunk_03"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Multi-hop single-paper reasoning chain (2 hops) across 2106.09685_LoRA."
    }
  },
  {
    "question_id": "gold_q32_multihop_single_roberta_dynamic_masking",
    "paper_ids": [
      "1907.11692_RoBERTa"
    ],
    "question": "How did dynamic masking in RoBERTa resolve the data repetition limitation of original static masking in BERT?",
    "category": "multi_hop_single_paper",
    "answerable": true,
    "gold_answers": [
      "In BERT, masking was performed once during data preprocessing and kept static across all epochs, exposing the model to the exact same masked tokens every time a sequence was repeated. RoBERTa introduced dynamic masking by generating a fresh random masking pattern every time a sequence was fed to the model, improving representation robustness across long pre-training runs."
    ],
    "gold_evidence": [
      {
        "paper_id": "1907.11692_RoBERTa",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "Section 2 / Methods",
        "quote": "The original BERT implementation performed masking once during data preprocessing, resulting in a single static mask."
      },
      {
        "paper_id": "1907.11692_RoBERTa",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "Section 3 / Analysis",
        "quote": "We implement dynamic masking where we generate the masking pattern every time we feed a sequence to the model, which is crucial when pretraining for more steps."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "static_preprocessing_mask",
          "dynamic_runtime_mask_generation",
          "roberta_representation_robustness"
        ],
        "edges": [
          {
            "source": "static_preprocessing_mask",
            "target": "dynamic_runtime_mask_generation",
            "type": "REPLACES_STATIC_WITH_PER_EPOCH_MASK",
            "paper_id": "1907.11692_RoBERTa",
            "chunk_id": "chunk_01"
          },
          {
            "source": "dynamic_runtime_mask_generation",
            "target": "roberta_representation_robustness",
            "type": "PREVENTS_TOKEN_REPRESENTATION_OVERFITTING",
            "paper_id": "1907.11692_RoBERTa",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Multi-hop single-paper reasoning chain (2 hops) across 1907.11692_RoBERTa."
    }
  },
  {
    "question_id": "gold_q33_multihop_single_flashattention_online_softmax",
    "paper_ids": [
      "2205.14135_FlashAttention"
    ],
    "question": "How does online softmax scaling enable FlashAttention to compute attention without materializing intermediate N x N attention matrices?",
    "category": "multi_hop_single_paper",
    "answerable": true,
    "gold_answers": [
      "Standard softmax requires two passes over the entire sequence to compute max m and sum of exponentials l. FlashAttention uses online softmax by maintaining running local maximums m^(new) = max(m^(old), m_block) and scaling factors l^(new) = exp(m^(old) - m^(new)) * l^(old) + exp(m_block - m^(new)), allowing attention outputs to be updated block by block in SRAM without storing the full N x N matrix in HBM."
    ],
    "gold_evidence": [
      {
        "paper_id": "2205.14135_FlashAttention",
        "chunk_id": "chunk_02",
        "page": 2,
        "section": "Section 2 / Methods",
        "quote": "The standard softmax requires multiple passes over the input to compute row-wise maximum and normalization constants."
      },
      {
        "paper_id": "2205.14135_FlashAttention",
        "chunk_id": "chunk_03",
        "page": 3,
        "section": "Section 3 / Analysis",
        "quote": "By tracking running row maximums and row sums, we can compute softmax incrementally across blocks in SRAM without materializing the N x N attention matrix."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "two_pass_standard_softmax",
          "running_max_and_sum_tracking",
          "incremental_sram_attention_output"
        ],
        "edges": [
          {
            "source": "two_pass_standard_softmax",
            "target": "running_max_and_sum_tracking",
            "type": "REPLACES_WITH_ONLINE_FORMULATION",
            "paper_id": "2205.14135_FlashAttention",
            "chunk_id": "chunk_02"
          },
          {
            "source": "running_max_and_sum_tracking",
            "target": "incremental_sram_attention_output",
            "type": "UPDATES_ACCUMULATOR_IN_SRAM",
            "paper_id": "2205.14135_FlashAttention",
            "chunk_id": "chunk_03"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Multi-hop single-paper reasoning chain (2 hops) across 2205.14135_FlashAttention."
    }
  },
  {
    "question_id": "gold_q34_multihop_single_gin_multiset_injective",
    "paper_ids": [
      "1810.00826_GIN"
    ],
    "question": "How does GIN prove that sum aggregation functions are injective over countable multisets compared to mean or max aggregation?",
    "category": "multi_hop_single_paper",
    "answerable": true,
    "gold_answers": [
      "GIN proves that mean aggregation only captures the proportion of element types rather than their cardinality, while max aggregation only captures whether a feature exists regardless of frequency. In contrast, modeling the multiset aggregation as h(c) = sum_{x in X} f(x) with learnable epsilon in h_v = MLP((1 + epsilon) h_v + sum_{u} h_u) is mathematically injective over countable multisets."
    ],
    "gold_evidence": [
      {
        "paper_id": "1810.00826_GIN",
        "chunk_id": "chunk_02",
        "page": 2,
        "section": "Section 2 / Methods",
        "quote": "Mean aggregation fails to distinguish multisets of different sizes with the same feature proportions, and max aggregation fails to distinguish multisets with different element counts."
      },
      {
        "paper_id": "1810.00826_GIN",
        "chunk_id": "chunk_03",
        "page": 3,
        "section": "Section 3 / Analysis",
        "quote": "We show that sum aggregation is injective on countable multisets: h(X) = sum_{x in X} f(x) can distinguish distinct multisets uniquely."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "failure_modes_of_mean_max",
          "injective_multiset_sum_theorem",
          "gin_universal_multiset_layer"
        ],
        "edges": [
          {
            "source": "failure_modes_of_mean_max",
            "target": "injective_multiset_sum_theorem",
            "type": "PROVES_NON_INJECTIVITY_OF_MEAN_MAX",
            "paper_id": "1810.00826_GIN",
            "chunk_id": "chunk_02"
          },
          {
            "source": "injective_multiset_sum_theorem",
            "target": "gin_universal_multiset_layer",
            "type": "CONSTRUCTS_INJECTIVE_SUM_MLP",
            "paper_id": "1810.00826_GIN",
            "chunk_id": "chunk_03"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Multi-hop single-paper reasoning chain (2 hops) across 1810.00826_GIN."
    }
  },
  {
    "question_id": "gold_q35_multihop_single_ddpm_variational_bound",
    "paper_ids": [
      "2006.11239_DDPM"
    ],
    "question": "How does DDPM decompose the negative log-likelihood variational bound into tractable KL divergence terms between Gaussian distributions?",
    "category": "multi_hop_single_paper",
    "answerable": true,
    "gold_answers": [
      "DDPM expresses the variational lower bound L_vlb as a sum of KL divergences L_t = D_{KL}(q(x_{t-1}|x_t, x_0) || p_theta(x_{t-1}|x_t)). Because the forward posterior q(x_{t-1}|x_t, x_0) conditioned on x_0 is an analytical Gaussian with closed-form mean tilde_mu_t and variance tilde_beta_t, all KL terms can be evaluated in closed form rather than estimated via high-variance Monte Carlo sampling."
    ],
    "gold_evidence": [
      {
        "paper_id": "2006.11239_DDPM",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "Section 2 / Methods",
        "quote": "The variational lower bound can be rewritten as a sum of KL divergence terms comparing the forward process posterior with the parameterized reverse process."
      },
      {
        "paper_id": "2006.11239_DDPM",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "Section 3 / Analysis",
        "quote": "Since q(x_{t-1} | x_t, x_0) is Gaussian, we can write down its parameters in closed form, making the KL divergence analytically computable."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "variational_lower_bound_decomposition",
          "conditioned_gaussian_posterior",
          "closed_form_kl_evaluation"
        ],
        "edges": [
          {
            "source": "variational_lower_bound_decomposition",
            "target": "conditioned_gaussian_posterior",
            "type": "REWRITES_TERMS_CONDITIONED_ON_X0",
            "paper_id": "2006.11239_DDPM",
            "chunk_id": "chunk_01"
          },
          {
            "source": "conditioned_gaussian_posterior",
            "target": "closed_form_kl_evaluation",
            "type": "EVALUATES_ANALYTIC_KL_DIVERGENCE",
            "paper_id": "2006.11239_DDPM",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Multi-hop single-paper reasoning chain (2 hops) across 2006.11239_DDPM."
    }
  },
  {
    "question_id": "gold_q36_multihop_single_clip_zero_shot_prompting",
    "paper_ids": [
      "2103.00020_CLIP"
    ],
    "question": "How does prompt engineering with natural language templates improve zero-shot classification in CLIP over raw class names?",
    "category": "multi_hop_single_paper",
    "answerable": true,
    "gold_answers": [
      "Using raw class labels (e.g. 'dog') suffers from polysemy and lack of visual context in the text encoder. Wrapping class names in prompt templates like 'A photo of a {label}, a type of pet' grounds the text embedding in visual photography concepts, yielding significant gains of over 5% in zero-shot Top-1 accuracy across ImageNet benchmarks."
    ],
    "gold_evidence": [
      {
        "paper_id": "2103.00020_CLIP",
        "chunk_id": "chunk_02",
        "page": 2,
        "section": "Section 2 / Methods",
        "quote": "A common issue is polysemy: when the text encoder is given just the word without context, it cannot distinguish meanings."
      },
      {
        "paper_id": "2103.00020_CLIP",
        "chunk_id": "chunk_03",
        "page": 3,
        "section": "Section 3 / Analysis",
        "quote": "Using the prompt template 'A photo of a {label}' helps specify that the text is about an image, improving accuracy on ImageNet by several percentage points."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "raw_label_polysemy",
          "prompt_template_visual_grounding",
          "zero_shot_accuracy_gain"
        ],
        "edges": [
          {
            "source": "raw_label_polysemy",
            "target": "prompt_template_visual_grounding",
            "type": "RESOLVES_AMBIGUITY_VIA_TEMPLATES",
            "paper_id": "2103.00020_CLIP",
            "chunk_id": "chunk_02"
          },
          {
            "source": "prompt_template_visual_grounding",
            "target": "zero_shot_accuracy_gain",
            "type": "BOOSTS_IMAGENET_ZERO_SHOT_METRICS",
            "paper_id": "2103.00020_CLIP",
            "chunk_id": "chunk_03"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Multi-hop single-paper reasoning chain (2 hops) across 2103.00020_CLIP."
    }
  },
  {
    "question_id": "gold_q37_multihop_single_react_error_correction",
    "paper_ids": [
      "2210.03629_ReAct"
    ],
    "question": "How does ReAct prevent error compounding during multi-hop question answering compared to pure Chain-of-Thought?",
    "category": "multi_hop_single_paper",
    "answerable": true,
    "gold_answers": [
      "In pure Chain-of-Thought, an initial erroneous hallucination propagates unchecked throughout subsequent reasoning steps without external validation. ReAct breaks this error loop by executing search actions against an external environment, using real observations to verify hypotheses and trigger corrective thoughts when retrieved facts conflict with initial assumptions."
    ],
    "gold_evidence": [
      {
        "paper_id": "2210.03629_ReAct",
        "chunk_id": "chunk_02",
        "page": 2,
        "section": "Section 2 / Methods",
        "quote": "Chain-of-thought suffers from error propagation: once an incorrect intermediate thought is generated, it leads to hallucinated answers."
      },
      {
        "paper_id": "2210.03629_ReAct",
        "chunk_id": "chunk_03",
        "page": 3,
        "section": "Section 3 / Analysis",
        "quote": "ReAct interleaves external observations that allow the model to detect and correct errors dynamically during execution."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "cot_error_propagation",
          "external_environment_observation",
          "dynamic_error_recovery_thought"
        ],
        "edges": [
          {
            "source": "cot_error_propagation",
            "target": "external_environment_observation",
            "type": "GROUNDS_REASONING_IN_EXTERNAL_FACTS",
            "paper_id": "2210.03629_ReAct",
            "chunk_id": "chunk_02"
          },
          {
            "source": "external_environment_observation",
            "target": "dynamic_error_recovery_thought",
            "type": "TRIGGERS_COURSE_CORRECTION_CYCLE",
            "paper_id": "2210.03629_ReAct",
            "chunk_id": "chunk_03"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Multi-hop single-paper reasoning chain (2 hops) across 2210.03629_ReAct."
    }
  },
  {
    "question_id": "gold_q38_multihop_single_dpo_gradient_dynamics",
    "paper_ids": [
      "2305.18290_DPO"
    ],
    "question": "How does the DPO gradient update modulate policy adjustments based on the implicit reward error of preferred and dispreferred completions?",
    "category": "multi_hop_single_paper",
    "answerable": true,
    "gold_answers": [
      "The gradient of the DPO objective weights policy parameter updates by the probability sigma(hat_r_theta(x, y_l) - hat_r_theta(x, y_w)), which acts as an adaptive learning rate: when the model currently assigns high reward to the winning completion y_w over losing completion y_l, the gradient weight approaches 0; when the model incorrectly prefers y_l, the gradient weight approaches 1 to heavily penalize the error."
    ],
    "gold_evidence": [
      {
        "paper_id": "2305.18290_DPO",
        "chunk_id": "chunk_02",
        "page": 2,
        "section": "Section 2 / Methods",
        "quote": "The gradient of the DPO loss can be analyzed as weighting updates by the implicit reward error."
      },
      {
        "paper_id": "2305.18290_DPO",
        "chunk_id": "chunk_03",
        "page": 3,
        "section": "Section 3 / Analysis",
        "quote": "When the model's implicit reward already favors y_w, the weight sigma(r_l - r_w) is small; when the model is wrong, the gradient strongly pushes to increase log-likelihood of y_w."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "dpo_implicit_reward_formulation",
          "adaptive_gradient_weight_factor",
          "error_dependent_policy_adjustment"
        ],
        "edges": [
          {
            "source": "dpo_implicit_reward_formulation",
            "target": "adaptive_gradient_weight_factor",
            "type": "DETERMINES_MARGIN_ERROR_SCALING",
            "paper_id": "2305.18290_DPO",
            "chunk_id": "chunk_02"
          },
          {
            "source": "adaptive_gradient_weight_factor",
            "target": "error_dependent_policy_adjustment",
            "type": "STRONGLY_UPDATES_MISCLASSIFIED_PAIRS",
            "paper_id": "2305.18290_DPO",
            "chunk_id": "chunk_03"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Multi-hop single-paper reasoning chain (2 hops) across 2305.18290_DPO."
    }
  },
  {
    "question_id": "gold_q39_cross_gcn_graphsage_spectral_to_spatial",
    "paper_ids": [
      "1609.02907_GCN",
      "1706.02216_GraphSAGE"
    ],
    "question": "Why is spectral GCN inherently transductive and how does GraphSAGE's localized sampling enable inductive generalization to unseen nodes?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "GCN requires the full graph Laplacian L = D^(-1/2) A D^(-1/2) during training, making it transductive and memory-intensive on large graphs because the entire adjacency matrix must reside in memory. GraphSAGE circumvents full-graph dependencies by sampling a fixed-size local neighborhood and learning parameter-shared aggregation functions, enabling inductive batch training on unseen graphs."
    ],
    "gold_evidence": [
      {
        "paper_id": "1609.02907_GCN",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "Our method scales linearly in the number of graph edges and learns hidden layer representations that encode both local graph structure and features of nodes."
      },
      {
        "paper_id": "1706.02216_GraphSAGE",
        "chunk_id": "chunk_02",
        "page": 2,
        "section": "2 Related Work",
        "quote": "Most GCN approaches are inherently transductive and require the full graph Laplacian during training. In contrast, our approach does not require the full graph during training and can generalize to completely unseen graphs."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "gcn_model",
          "full_graph_laplacian",
          "graphsage_framework",
          "fixed_size_neighborhood_sampling"
        ],
        "edges": [
          {
            "source": "gcn_model",
            "target": "full_graph_laplacian",
            "type": "REQUIRES_FULL_MATRIX",
            "paper_id": "1609.02907_GCN",
            "chunk_id": "chunk_01"
          },
          {
            "source": "full_graph_laplacian",
            "target": "graphsage_framework",
            "type": "MOTIVATES_INDUCTIVE_ADVANCE",
            "paper_id": "1706.02216_GraphSAGE",
            "chunk_id": "chunk_02"
          },
          {
            "source": "graphsage_framework",
            "target": "fixed_size_neighborhood_sampling",
            "type": "SCALES_VIA_SAMPLING",
            "paper_id": "1706.02216_GraphSAGE",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 3,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (3 hops) linking 1609.02907_GCN, 1706.02216_GraphSAGE."
    }
  },
  {
    "question_id": "gold_q40_cross_bert_rag_dpr_dual_encoder",
    "paper_ids": [
      "1810.04805_BERT",
      "2004.04906_DPR",
      "2005.11401_RAG"
    ],
    "question": "How does the bidirectional representation learned by BERT power the dual-encoder retrieval mechanism in DPR and the non-parametric memory of RAG?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "BERT provides the deep bidirectional contextual token representations used by DPR to initialize its question encoder E_Q and passage encoder E_P. DPR pre-trains these bi-encoders to maximize inner products of relevant pairs, and RAG integrates this DPR index as its non-parametric memory layer coupled to a sequence-to-sequence generator."
    ],
    "gold_evidence": [
      {
        "paper_id": "1810.04805_BERT",
        "chunk_id": "chunk_01",
        "page": 1,
        "section": "1 Introduction",
        "quote": "BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context."
      },
      {
        "paper_id": "2004.04906_DPR",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "2 Dense Passage Retriever",
        "quote": "DPR uses two independent BERT encoders: one for passages and one for questions."
      },
      {
        "paper_id": "2005.11401_RAG",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "2 Methods",
        "quote": "The non-parametric memory consists of a dense vector index of Wikipedia passages, retrieved via Dense Passage Retriever (DPR)."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "bert_bidirectional",
          "dpr_dual_encoder_bert",
          "rag_non_parametric_index"
        ],
        "edges": [
          {
            "source": "bert_bidirectional",
            "target": "dpr_dual_encoder_bert",
            "type": "INITIALIZES_DUAL_ENCODERS",
            "paper_id": "2004.04906_DPR",
            "chunk_id": "chunk_01"
          },
          {
            "source": "dpr_dual_encoder_bert",
            "target": "rag_non_parametric_index",
            "type": "POWERS_RETRIEVAL_INDEX",
            "paper_id": "2005.11401_RAG",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 1810.04805_BERT, 2004.04906_DPR, 2005.11401_RAG."
    }
  },
  {
    "question_id": "gold_q41_cross_vaswani_flashattention_exactness",
    "paper_ids": [
      "1706.03762_Attention_Is_All_You_Need",
      "2205.14135_FlashAttention"
    ],
    "question": "How does FlashAttention preserve the exact mathematical attention output of the original Transformer while eliminating quadratic memory footprint?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "Vaswani et al. formulated attention as Softmax((Q K^T) / sqrt(d_k)) V, which creates an intermediate N x N attention matrix requiring O(N^2) HBM memory. FlashAttention preserves the exact same numeric softmax output using online softmax tiling across GPU SRAM blocks, eliminating O(N^2) HBM allocation while remaining mathematically equivalent."
    ],
    "gold_evidence": [
      {
        "paper_id": "1706.03762_Attention_Is_All_You_Need",
        "chunk_id": "chunk_03",
        "page": 3,
        "section": "3.2.1 Scaled Dot-Product Attention",
        "quote": "We compute the dot products of the query with all keys, divide each by sqrt(d_k), and apply a softmax function to obtain the weights on the values."
      },
      {
        "paper_id": "2205.14135_FlashAttention",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "FlashAttention computes exact attention with fewer memory accesses by tiling without materializing the large N x N attention matrix."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "vaswani_softmax_attention",
          "quadratic_intermediate_matrix",
          "flashattention_online_tiling"
        ],
        "edges": [
          {
            "source": "vaswani_softmax_attention",
            "target": "quadratic_intermediate_matrix",
            "type": "MATERIALIZES_O_N2_MATRIX",
            "paper_id": "1706.03762_Attention_Is_All_You_Need",
            "chunk_id": "chunk_03"
          },
          {
            "source": "quadratic_intermediate_matrix",
            "target": "flashattention_online_tiling",
            "type": "REPLACED_BY_EXACT_BLOCK_TILING",
            "paper_id": "2205.14135_FlashAttention",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 1706.03762_Attention_Is_All_You_Need, 2205.14135_FlashAttention."
    }
  },
  {
    "question_id": "gold_q42_cross_bert_roberta_pretraining_refinements",
    "paper_ids": [
      "1810.04805_BERT",
      "1907.11692_RoBERTa"
    ],
    "question": "How did RoBERTa systematically demonstrate that BERT was significantly undertrained and what components were eliminated?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "While BERT included Next Sentence Prediction (NSP) alongside Masked Language Modeling and used static masking on 16GB of text, RoBERTa systematically demonstrated that removing NSP actually improves downstream performance, and that training longer with dynamic masking over 160GB of data dramatically surpassed all original BERT benchmarks."
    ],
    "gold_evidence": [
      {
        "paper_id": "1810.04805_BERT",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "3.1 Pre-training Tasks",
        "quote": "We pre-train BERT using two unsupervised tasks: Masked LM and Next Sentence Prediction."
      },
      {
        "paper_id": "1907.11692_RoBERTa",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "We find that BERT was significantly undertrained. Removing the next sentence prediction objective matches or slightly improves downstream performance."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "bert_nsp_and_static_masking",
          "roberta_replication_study",
          "elimination_of_nsp_and_dynamic_scaling"
        ],
        "edges": [
          {
            "source": "bert_nsp_and_static_masking",
            "target": "roberta_replication_study",
            "type": "EVALUATED_IN_ABLATION_STUDY",
            "paper_id": "1907.11692_RoBERTa",
            "chunk_id": "chunk_01"
          },
          {
            "source": "roberta_replication_study",
            "target": "elimination_of_nsp_and_dynamic_scaling",
            "type": "REMOVES_NSP_AND_SCALES_DATA",
            "paper_id": "1907.11692_RoBERTa",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 1810.04805_BERT, 1907.11692_RoBERTa."
    }
  },
  {
    "question_id": "gold_q43_cross_deepwalk_node2vec_search_generalization",
    "paper_ids": [
      "1403.6652_DeepWalk",
      "1607.00653_node2vec"
    ],
    "question": "In what theoretical manner does node2vec generalize the uniform random walk exploration strategy of DeepWalk?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "DeepWalk generates uniform random walks where transition probabilities are unweighted and independent of history (first-order Markov chain). node2vec generalizes this by introducing a second-order random walk parameterized by p and q, where setting p=1 and q=1 strictly recovers DeepWalk's uniform random walk as a special case."
    ],
    "gold_evidence": [
      {
        "paper_id": "1403.6652_DeepWalk",
        "chunk_id": "chunk_01",
        "page": 3,
        "section": "3 DeepWalk",
        "quote": "We generate random walks using a uniform distribution over the neighbors of the current vertex."
      },
      {
        "paper_id": "1607.00653_node2vec",
        "chunk_id": "chunk_02",
        "page": 4,
        "section": "3.2 node2vec Walk",
        "quote": "Notice that when p=1 and q=1, the transition probabilities alpha_{pq}(t, x) are identical, and our random walk strategy reduces to DeepWalk."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "deepwalk_uniform_walks",
          "second_order_parametric_walk",
          "node2vec_generalization"
        ],
        "edges": [
          {
            "source": "deepwalk_uniform_walks",
            "target": "second_order_parametric_walk",
            "type": "GENERALIZED_BY_P_Q_BIAS",
            "paper_id": "1607.00653_node2vec",
            "chunk_id": "chunk_02"
          },
          {
            "source": "second_order_parametric_walk",
            "target": "node2vec_generalization",
            "type": "RECOVERS_DEEPWALK_AT_P1_Q1",
            "paper_id": "1607.00653_node2vec",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 1403.6652_DeepWalk, 1607.00653_node2vec."
    }
  },
  {
    "question_id": "gold_q44_cross_gcn_gat_spectral_to_anisotropic",
    "paper_ids": [
      "1609.02907_GCN",
      "1710.10903_GAT"
    ],
    "question": "How does GAT replace the isotropic fixed-degree normalization of GCN with anisotropic attention-weighted aggregation?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "GCN weights neighbor messages using fixed structural constants 1 / sqrt(deg(i) * deg(j)) based purely on graph degrees, assigning identical importance to all neighbors of the same degree (isotropic). GAT replaces this with dynamic self-attention coefficients alpha_ij conditioned on node feature embeddings, allowing the model to attend to different neighbors with varying importance (anisotropic)."
    ],
    "gold_evidence": [
      {
        "paper_id": "1609.02907_GCN",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "2 Methods",
        "quote": "We use symmetric degree normalization D_tilde^(-1/2) A_tilde D_tilde^(-1/2) to scale neighbor feature contributions."
      },
      {
        "paper_id": "1710.10903_GAT",
        "chunk_id": "chunk_01",
        "page": 1,
        "section": "1 Introduction",
        "quote": "GCN assigns static weights based on graph structure. Our attention architecture allows for assigning different importances to nodes of a same neighborhood."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "gcn_degree_normalization",
          "isotropic_aggregation_limitation",
          "gat_anisotropic_attention"
        ],
        "edges": [
          {
            "source": "gcn_degree_normalization",
            "target": "isotropic_aggregation_limitation",
            "type": "APPLIES_STATIC_DEGREE_WEIGHTS",
            "paper_id": "1609.02907_GCN",
            "chunk_id": "chunk_02"
          },
          {
            "source": "isotropic_aggregation_limitation",
            "target": "gat_anisotropic_attention",
            "type": "REPLACED_BY_DYNAMIC_ATTENTION_WEIGHTS",
            "paper_id": "1710.10903_GAT",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 1609.02907_GCN, 1710.10903_GAT."
    }
  },
  {
    "question_id": "gold_q45_cross_cot_react_hallucination_mitigation",
    "paper_ids": [
      "2201.11903_Chain_of_Thought",
      "2210.03629_ReAct"
    ],
    "question": "Why does Chain-of-Thought suffer from ungrounded hallucination on factual questions and how does ReAct synergize reasoning with environment interactions to ground claims?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "Chain-of-Thought relies entirely on internal parametric knowledge, meaning factually incorrect hallucinations in early reasoning steps cannot be fact-checked and propagate into false conclusions. ReAct synergizes CoT reasoning traces with external actions (e.g. search queries), using external observations to verify factual assertions before proceeding."
    ],
    "gold_evidence": [
      {
        "paper_id": "2201.11903_Chain_of_Thought",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "Chain-of-thought prompting generates a sequence of intermediate reasoning steps entirely from the language model's weights."
      },
      {
        "paper_id": "2210.03629_ReAct",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "CoT is a static black box without access to external worlds, leading to hallucination. ReAct interleaves reasoning traces with external actions to inspect facts."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "cot_isolated_reasoning",
          "hallucination_vulnerability",
          "react_grounded_action_loop"
        ],
        "edges": [
          {
            "source": "cot_isolated_reasoning",
            "target": "hallucination_vulnerability",
            "type": "LACKS_FACTUAL_GROUNDING",
            "paper_id": "2201.11903_Chain_of_Thought",
            "chunk_id": "chunk_01"
          },
          {
            "source": "hallucination_vulnerability",
            "target": "react_grounded_action_loop",
            "type": "GROUNDED_BY_INTERLEAVED_ACTIONS",
            "paper_id": "2210.03629_ReAct",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 2201.11903_Chain_of_Thought, 2210.03629_ReAct."
    }
  },
  {
    "question_id": "gold_q46_cross_lora_dpo_parameter_efficient_alignment",
    "paper_ids": [
      "2106.09685_LoRA",
      "2305.18290_DPO"
    ],
    "question": "How does combining Low-Rank Adaptation (LoRA) with Direct Preference Optimization (DPO) democratize LLM preference alignment?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "Standard DPO eliminates the reward model but still requires loading base and reference policy models into GPU VRAM. When combined with LoRA, the reference policy is represented by the frozen base weights while only low-rank matrices A and B are trained for the active policy, dramatically reducing VRAM usage and enabling consumer GPU alignment."
    ],
    "gold_evidence": [
      {
        "paper_id": "2106.09685_LoRA",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "LoRA freezes the pre-trained model weights and injects trainable rank decomposition matrices, reducing trainable parameters by up to 10,000 times."
      },
      {
        "paper_id": "2305.18290_DPO",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "DPO directly optimizes policy pi_theta relative to reference policy pi_ref without training an explicit reward model."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "dpo_dual_policy_memory_requirement",
          "lora_frozen_base_adapter",
          "efficient_consumer_gpu_alignment"
        ],
        "edges": [
          {
            "source": "dpo_dual_policy_memory_requirement",
            "target": "lora_frozen_base_adapter",
            "type": "USES_FROZEN_BASE_AS_PI_REF",
            "paper_id": "2305.18290_DPO",
            "chunk_id": "chunk_01"
          },
          {
            "source": "lora_frozen_base_adapter",
            "target": "efficient_consumer_gpu_alignment",
            "type": "MINIMIZES_VRAM_ALLOCATION",
            "paper_id": "2106.09685_LoRA",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 2106.09685_LoRA, 2305.18290_DPO."
    }
  },
  {
    "question_id": "gold_q47_cross_gcn_gin_expressive_power",
    "paper_ids": [
      "1609.02907_GCN",
      "1810.00826_GIN"
    ],
    "question": "Why does GCN fail to distinguish non-isomorphic graph structures that GIN can distinguish according to Weisfeiler-Lehman analysis?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "GCN's aggregation is mathematically equivalent to a weighted mean aggregator followed by linear transformation. As proven by Xu et al. in the GIN paper, mean aggregators fail to distinguish multisets of different sizes that share the same node feature proportions, whereas GIN's sum aggregator is injective and achieves the full expressive power of the 1-WL test."
    ],
    "gold_evidence": [
      {
        "paper_id": "1609.02907_GCN",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "2 Methods",
        "quote": "The layer-wise propagation rule computes a normalized weighted average of neighbor features."
      },
      {
        "paper_id": "1810.00826_GIN",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "3 Expressive Power",
        "quote": "Mean aggregators cannot distinguish graphs whose node neighborhoods have identical feature distributions but different cardinalities."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "gcn_mean_style_aggregation",
          "multiset_cardinality_blindness",
          "gin_injective_sum_aggregator"
        ],
        "edges": [
          {
            "source": "gcn_mean_style_aggregation",
            "target": "multiset_cardinality_blindness",
            "type": "LOSES_GRAPH_SIZE_INFORMATION",
            "paper_id": "1609.02907_GCN",
            "chunk_id": "chunk_02"
          },
          {
            "source": "multiset_cardinality_blindness",
            "target": "gin_injective_sum_aggregator",
            "type": "RESOLVED_BY_INJECTIVE_SUM_MAPPING",
            "paper_id": "1810.00826_GIN",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 1609.02907_GCN, 1810.00826_GIN."
    }
  },
  {
    "question_id": "gold_q48_cross_transe_mecch_heterogeneous_relations",
    "paper_ids": [
      "1703.08098_KG_Embedding_Survey",
      "2211.12792_MECCH"
    ],
    "question": "How does MECCH extend static knowledge graph translational embeddings like TransE into contextual graph neural network message-passing?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "TransE optimizes static translational distance vectors h + r approx t independently for each triple without conditioning on complex neighborhood topologies or multi-relational metapaths. MECCH elevates heterogeneous relations into metapath contexts, using convolutional aggregation and attention across metapath walks to dynamically contextualize representations."
    ],
    "gold_evidence": [
      {
        "paper_id": "1703.08098_KG_Embedding_Survey",
        "chunk_id": "chunk_02",
        "page": 4,
        "section": "3.1 Models",
        "quote": "TransE models relations as simple linear translations between entity pairs in vector space."
      },
      {
        "paper_id": "2211.12792_MECCH",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "MECCH leverages metapath context convolutions to capture high-order semantics across diverse heterogeneous relation paths."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "transe_static_triplets",
          "isolated_triple_limitation",
          "mecch_metapath_context_convolution"
        ],
        "edges": [
          {
            "source": "transe_static_triplets",
            "target": "isolated_triple_limitation",
            "type": "NEGLECTS_HIGH_ORDER_PATHWAYS",
            "paper_id": "1703.08098_KG_Embedding_Survey",
            "chunk_id": "chunk_02"
          },
          {
            "source": "isolated_triple_limitation",
            "target": "mecch_metapath_context_convolution",
            "type": "CONVOLVES_ALONG_METAPATHS",
            "paper_id": "2211.12792_MECCH",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 1703.08098_KG_Embedding_Survey, 2211.12792_MECCH."
    }
  },
  {
    "question_id": "gold_q49_cross_ddpm_clip_guided_diffusion",
    "paper_ids": [
      "2006.11239_DDPM",
      "2103.00020_CLIP"
    ],
    "question": "How does the joint multimodal embedding space of CLIP provide guiding gradients for denoising diffusion probabilistic models (DDPM)?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "DDPM models unconditional or class-conditional reverse diffusion using predicted noise epsilon_theta. By computing the gradient of CLIP's cosine similarity between an encoded target text prompt and the predicted clean image x_0 with respect to the noisy intermediate latent x_t, CLIP provides guiding gradients that steer the reverse diffusion process toward generating images matching the text prompt."
    ],
    "gold_evidence": [
      {
        "paper_id": "2006.11239_DDPM",
        "chunk_id": "chunk_02",
        "page": 4,
        "section": "3 Methods",
        "quote": "The reverse process is trained to estimate noise epsilon using a parameterized neural network epsilon_theta."
      },
      {
        "paper_id": "2103.00020_CLIP",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "2 Methods",
        "quote": "CLIP creates a shared multimodal embedding space where image and text embeddings have high cosine similarity when semantically aligned."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "ddpm_latent_generation",
          "clip_shared_multimodal_space",
          "clip_gradient_guided_diffusion"
        ],
        "edges": [
          {
            "source": "ddpm_latent_generation",
            "target": "clip_shared_multimodal_space",
            "type": "MAPS_INTERMEDIATE_LATENTS_TO_TEXT",
            "paper_id": "2006.11239_DDPM",
            "chunk_id": "chunk_02"
          },
          {
            "source": "clip_shared_multimodal_space",
            "target": "clip_gradient_guided_diffusion",
            "type": "PROVIDES_GUIDANCE_GRADIENTS",
            "paper_id": "2103.00020_CLIP",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 2006.11239_DDPM, 2103.00020_CLIP."
    }
  },
  {
    "question_id": "gold_q50_cross_dpr_rag_end_to_end_backpropagation",
    "paper_ids": [
      "2004.04906_DPR",
      "2005.11401_RAG"
    ],
    "question": "Can the dense retriever component in RAG be fine-tuned via gradients backpropagated from the sequence-to-sequence language model?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "Yes; while DPR was originally pre-trained as a standalone retrieval model using negative passage contrastive loss, RAG treats the retrieval step p(z|x) as a differentiable latent variable layer, allowing gradients from the sequence generator loss to backpropagate into the query encoder E_Q to fine-tune retrieval specifically for downstream generation tasks."
    ],
    "gold_evidence": [
      {
        "paper_id": "2004.04906_DPR",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "2 Approach",
        "quote": "DPR is trained using in-batch negatives and BM25 hard negatives with cross-entropy loss on passage selection."
      },
      {
        "paper_id": "2005.11401_RAG",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "2 Architecture",
        "quote": "We can fine-tune the DPR retriever and the seq2seq generator end-to-end without direct supervision on which document should be retrieved."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "dpr_standalone_contrastive_pretraining",
          "differentiable_latent_retrieval_layer",
          "end_to_end_generator_backpropagation"
        ],
        "edges": [
          {
            "source": "dpr_standalone_contrastive_pretraining",
            "target": "differentiable_latent_retrieval_layer",
            "type": "EMBEDDED_AS_LATENT_PRIOR",
            "paper_id": "2004.04906_DPR",
            "chunk_id": "chunk_01"
          },
          {
            "source": "differentiable_latent_retrieval_layer",
            "target": "end_to_end_generator_backpropagation",
            "type": "BACKPROPAGATES_GENERATION_LOSS",
            "paper_id": "2005.11401_RAG",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 2004.04906_DPR, 2005.11401_RAG."
    }
  },
  {
    "question_id": "gold_q51_cross_transformer_gat_attention_mechanisms",
    "paper_ids": [
      "1706.03762_Attention_Is_All_You_Need",
      "1710.10903_GAT"
    ],
    "question": "Compare the attention formulation in Transformer (Scaled Dot-Product) with Graph Attention Networks (GAT Additive Attention).",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "Vaswani et al. use multiplicative scaled dot-product attention Softmax(Q K^T / sqrt(d_k)) where queries and keys interact through matrix multiplication scaled by dimension. In contrast, Veli\u010dkovi\u0107 et al. use additive attention where transformed features Wh_i and Wh_j are concatenated, multiplied by a weight vector a, passed through LeakyReLU, and normalized across neighbors."
    ],
    "gold_evidence": [
      {
        "paper_id": "1706.03762_Attention_Is_All_You_Need",
        "chunk_id": "chunk_03",
        "page": 3,
        "section": "3.2.1 Scaled Dot-Product",
        "quote": "We compute the dot products of the query with all keys, divide each by sqrt(d_k), and apply a softmax function."
      },
      {
        "paper_id": "1710.10903_GAT",
        "chunk_id": "chunk_02",
        "page": 2,
        "section": "2.1 Attentional Layer",
        "quote": "The attentional mechanism a is a single-layer feedforward neural network, applied with LeakyReLU non-linearity on concatenated transformed features."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "transformer_multiplicative_dot_product",
          "structural_attention_comparison",
          "gat_additive_leakyrelu_attention"
        ],
        "edges": [
          {
            "source": "transformer_multiplicative_dot_product",
            "target": "structural_attention_comparison",
            "type": "DIFFERS_IN_INTERACTION_FUNCTION",
            "paper_id": "1706.03762_Attention_Is_All_You_Need",
            "chunk_id": "chunk_03"
          },
          {
            "source": "structural_attention_comparison",
            "target": "gat_additive_leakyrelu_attention",
            "type": "USES_CONCATENATION_AND_LEAKYRELU",
            "paper_id": "1710.10903_GAT",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 1706.03762_Attention_Is_All_You_Need, 1710.10903_GAT."
    }
  },
  {
    "question_id": "gold_q52_cross_graphsage_gat_neighbor_aggregation",
    "paper_ids": [
      "1706.02216_GraphSAGE",
      "1710.10903_GAT"
    ],
    "question": "How does GAT's attention-based aggregation overcome the need for explicit random neighborhood sub-sampling used in GraphSAGE?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "GraphSAGE uniformly samples a fixed number of neighbors per layer (e.g. 25 at depth 1, 10 at depth 2) to control computation memory on high-degree hubs. GAT processes all immediate neighbors without sub-sampling by assigning dynamic attention weights alpha_ij that naturally attenuate irrelevant neighbors, avoiding information loss from arbitrary sub-sampling."
    ],
    "gold_evidence": [
      {
        "paper_id": "1706.02216_GraphSAGE",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "3 Methods",
        "quote": "We uniformly sample a fixed-size set of neighbors rather than using the full neighborhood to keep memory consumption bounded."
      },
      {
        "paper_id": "1710.10903_GAT",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "Our approach does not require any sampling of nodes or edges; instead, attention coefficients implicitly determine importance across neighbors."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "graphsage_uniform_subsampling",
          "neighbor_selection_tradeoff",
          "gat_implicit_attention_weighting"
        ],
        "edges": [
          {
            "source": "graphsage_uniform_subsampling",
            "target": "neighbor_selection_tradeoff",
            "type": "DROPS_NEIGHBORS_RANDOMLY",
            "paper_id": "1706.02216_GraphSAGE",
            "chunk_id": "chunk_02"
          },
          {
            "source": "neighbor_selection_tradeoff",
            "target": "gat_implicit_attention_weighting",
            "type": "PRESERVES_ALL_EDGES_VIA_WEIGHTS",
            "paper_id": "1710.10903_GAT",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 1706.02216_GraphSAGE, 1710.10903_GAT."
    }
  },
  {
    "question_id": "gold_q53_cross_bert_cot_reasoning_vs_pattern",
    "paper_ids": [
      "1810.04805_BERT",
      "2201.11903_Chain_of_Thought"
    ],
    "question": "Contrast BERT's masked contextual representation paradigm with Chain-of-Thought prompting for multi-step algorithmic deduction.",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "BERT performs non-autoregressive masked token prediction across a fixed 512-token context window, making it suitable for classification and extraction but incapable of multi-step sequential algorithmic deduction. CoT prompting utilizes autoregressive generative transformers to externalize reasoning steps as an explicit causal token chain, enabling multi-step problem solving."
    ],
    "gold_evidence": [
      {
        "paper_id": "1810.04805_BERT",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "BERT is trained to predict masked tokens bidirectionally, producing rich contextual representations for classification."
      },
      {
        "paper_id": "2201.11903_Chain_of_Thought",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "Generating a chain of thought allows the model to decompose complex problems into multi-step intermediate reasoning steps."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "bert_bidirectional_classification",
          "computational_paradigm_comparison",
          "cot_autoregressive_stepwise_reasoning"
        ],
        "edges": [
          {
            "source": "bert_bidirectional_classification",
            "target": "computational_paradigm_comparison",
            "type": "CONSTRAINED_TO_STATIC_LAYER_DEPTH",
            "paper_id": "1810.04805_BERT",
            "chunk_id": "chunk_01"
          },
          {
            "source": "computational_paradigm_comparison",
            "target": "cot_autoregressive_stepwise_reasoning",
            "type": "EXPANDS_DYNAMIC_REASONING_LENGTH",
            "paper_id": "2201.11903_Chain_of_Thought",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 1810.04805_BERT, 2201.11903_Chain_of_Thought."
    }
  },
  {
    "question_id": "gold_q54_cross_roberta_lora_efficient_adaptation",
    "paper_ids": [
      "1907.11692_RoBERTa",
      "2106.09685_LoRA"
    ],
    "question": "How does applying LoRA adaptation to RoBERTa compare with full fine-tuning on GLUE benchmarks in terms of parameter storage and performance?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "As shown by Hu et al., applying LoRA to RoBERTa-large with rank r=8 matches or exceeds full fine-tuning performance across GLUE tasks while training only 0.8M parameters instead of all 355M parameters, reducing checkpoint storage by over 400x and eliminating task-specific optimizer state bloat."
    ],
    "gold_evidence": [
      {
        "paper_id": "1907.11692_RoBERTa",
        "chunk_id": "chunk_01",
        "page": 3,
        "section": "1 Introduction",
        "quote": "RoBERTa establishes state-of-the-art results on GLUE benchmarks across 355M parameters."
      },
      {
        "paper_id": "2106.09685_LoRA",
        "chunk_id": "chunk_02",
        "page": 4,
        "section": "5 Empirical Evaluation",
        "quote": "When applying LoRA to RoBERTa-large, we match full fine-tuning on GLUE with 0.8M trainable parameters instead of 355M."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "roberta_full_finetuning_baseline",
          "adapter_parameter_comparison",
          "lora_rank_8_roberta_match"
        ],
        "edges": [
          {
            "source": "roberta_full_finetuning_baseline",
            "target": "adapter_parameter_comparison",
            "type": "REQUIRES_355M_UPDATED_WEIGHTS",
            "paper_id": "1907.11692_RoBERTa",
            "chunk_id": "chunk_01"
          },
          {
            "source": "adapter_parameter_comparison",
            "target": "lora_rank_8_roberta_match",
            "type": "TRAINS_0_8M_LOW_RANK_PARAMETERS",
            "paper_id": "2106.09685_LoRA",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 1907.11692_RoBERTa, 2106.09685_LoRA."
    }
  },
  {
    "question_id": "gold_q55_cross_flashattention_transformer_context_scaling",
    "paper_ids": [
      "1706.03762_Attention_Is_All_You_Need",
      "2205.14135_FlashAttention"
    ],
    "question": "How did FlashAttention enable Transformer sequence lengths to scale beyond the original 512-token limit of Vaswani et al. to 16k+ tokens?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "Vaswani et al. evaluated Transformers on sequence lengths of only a few hundred tokens because standard PyTorch attention requires O(N^2) memory in GPU high-bandwidth memory (HBM). By tiling Q, K, V and computing softmax incrementally in SRAM, FlashAttention scaled memory footprint from quadratic O(N^2) to linear O(N) in sequence length, enabling 16k-64k contexts on identical GPU hardware."
    ],
    "gold_evidence": [
      {
        "paper_id": "1706.03762_Attention_Is_All_You_Need",
        "chunk_id": "chunk_02",
        "page": 2,
        "section": "3.1 Model Architecture",
        "quote": "We train models with maximum sequence length of 512 tokens due to memory constraints."
      },
      {
        "paper_id": "2205.14135_FlashAttention",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "FlashAttention yields linear memory in sequence length instead of quadratic memory, enabling sequence lengths up to 64k tokens."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "vaswani_512_token_limit",
          "hbm_memory_bottleneck",
          "flashattention_linear_memory_scaling"
        ],
        "edges": [
          {
            "source": "vaswani_512_token_limit",
            "target": "hbm_memory_bottleneck",
            "type": "BOUND_BY_QUADRATIC_ALLOCATION",
            "paper_id": "1706.03762_Attention_Is_All_You_Need",
            "chunk_id": "chunk_02"
          },
          {
            "source": "hbm_memory_bottleneck",
            "target": "flashattention_linear_memory_scaling",
            "type": "OVERCOME_BY_ONLINE_SRAM_TILING",
            "paper_id": "2205.14135_FlashAttention",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 1706.03762_Attention_Is_All_You_Need, 2205.14135_FlashAttention."
    }
  },
  {
    "question_id": "gold_q56_cross_node2vec_gin_structural_role",
    "paper_ids": [
      "1607.00653_node2vec",
      "1810.00826_GIN"
    ],
    "question": "How do node2vec's structural equivalences discovered via BFS exploration relate to GIN's ability to distinguish structural roles in graphs?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "In node2vec, setting a high in-out parameter q forces random walks to explore local micro-structures (BFS-like), embedding nodes with similar local roles into proximity regardless of global network distance. In GIN, structural role distinction is formalized through multiset injectivity, proving that sum-aggregation preserves multiset structure while mean aggregation averages away local structural roles."
    ],
    "gold_evidence": [
      {
        "paper_id": "1607.00653_node2vec",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "3 Approach",
        "quote": "A low value of p and high value of q encourages BFS-like exploration, capturing structural equivalence and local roles."
      },
      {
        "paper_id": "1810.00826_GIN",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "3 Expressive Power",
        "quote": "Sum-based aggregation uniquely captures structural roles and multiset topologies that mean aggregators collapse."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "node2vec_bfs_structural_role",
          "structural_equivalence_concept",
          "gin_injective_role_preservation"
        ],
        "edges": [
          {
            "source": "node2vec_bfs_structural_role",
            "target": "structural_equivalence_concept",
            "type": "CAPTURES_MICROSTRUCTURE_ROLES",
            "paper_id": "1607.00653_node2vec",
            "chunk_id": "chunk_02"
          },
          {
            "source": "structural_equivalence_concept",
            "target": "gin_injective_role_preservation",
            "type": "FORMALIZED_VIA_INJECTIVE_AGGREGATION",
            "paper_id": "1810.00826_GIN",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 1607.00653_node2vec, 1810.00826_GIN."
    }
  },
  {
    "question_id": "gold_q57_cross_clip_react_multimodal_agents",
    "paper_ids": [
      "2103.00020_CLIP",
      "2210.03629_ReAct"
    ],
    "question": "How can a multimodal agent architecture combine CLIP zero-shot perception with ReAct action-observation loops?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "In a multimodal agent, CLIP serves as the perceptual tool that translates visual inputs into semantic zero-shot image embeddings and classification candidate scores. These scores are returned as environmental observations to a ReAct language model controller, which uses intermediate reasoning thoughts to decide whether to search for more images, refine prompts, or return the final answer."
    ],
    "gold_evidence": [
      {
        "paper_id": "2103.00020_CLIP",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "CLIP matches visual concepts to arbitrary natural language descriptions in a zero-shot manner."
      },
      {
        "paper_id": "2210.03629_ReAct",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "ReAct controller generates thoughts to plan and actions to query external tools, receiving observations back."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "clip_visual_observation_tool",
          "multimodal_agent_architecture",
          "react_controller_thought_cycle"
        ],
        "edges": [
          {
            "source": "clip_visual_observation_tool",
            "target": "multimodal_agent_architecture",
            "type": "FEEDS_ZERO_SHOT_SCORES_AS_OBSERVATION",
            "paper_id": "2103.00020_CLIP",
            "chunk_id": "chunk_01"
          },
          {
            "source": "multimodal_agent_architecture",
            "target": "react_controller_thought_cycle",
            "type": "UPDATES_REASONING_CHAIN_WITH_PERCEPTION",
            "paper_id": "2210.03629_ReAct",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 2103.00020_CLIP, 2210.03629_ReAct."
    }
  },
  {
    "question_id": "gold_q58_cross_ddpm_transformer_diffusion_backbone",
    "paper_ids": [
      "1706.03762_Attention_Is_All_You_Need",
      "2006.11239_DDPM"
    ],
    "question": "How do modern diffusion models substitute the U-Net backbone of DDPM with Transformer self-attention blocks?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "While Ho et al. implemented DDPM's noise prediction model epsilon_theta using a convolutional U-Net with Wide-ResNet blocks, later diffusion architectures replace convolutional spatial feature maps with sequences of flattened image patch tokens processed by standard Transformer self-attention layers as designed by Vaswani et al., allowing diffusion scaling to mirror LLM scaling laws."
    ],
    "gold_evidence": [
      {
        "paper_id": "2006.11239_DDPM",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "3 Model Architecture",
        "quote": "Our neural network architecture is a U-Net based on Wide-ResNet with self-attention at 16x16 resolution."
      },
      {
        "paper_id": "1706.03762_Attention_Is_All_You_Need",
        "chunk_id": "chunk_02",
        "page": 2,
        "section": "3 Model Architecture",
        "quote": "The Transformer uses stacked self-attention and point-wise fully connected layers for sequence modeling."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "ddpm_unet_convolutional_backbone",
          "diffusion_backbone_evolution",
          "transformer_patch_self_attention"
        ],
        "edges": [
          {
            "source": "ddpm_unet_convolutional_backbone",
            "target": "diffusion_backbone_evolution",
            "type": "REPLACED_CONVOLUTIONS_WITH_PATCH_TOKENS",
            "paper_id": "2006.11239_DDPM",
            "chunk_id": "chunk_02"
          },
          {
            "source": "diffusion_backbone_evolution",
            "target": "transformer_patch_self_attention",
            "type": "APPLIES_VASWANI_SELF_ATTENTION",
            "paper_id": "1706.03762_Attention_Is_All_You_Need",
            "chunk_id": "chunk_02"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 1706.03762_Attention_Is_All_You_Need, 2006.11239_DDPM."
    }
  },
  {
    "question_id": "gold_q59_cross_dpo_react_interactive_alignment",
    "paper_ids": [
      "2210.03629_ReAct",
      "2305.18290_DPO"
    ],
    "question": "How can DPO preference optimization be applied to trajectory logs of ReAct reasoning agents to reduce tool invocation hallucinations?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "Given two trajectory completions for the same query where one trajectory includes unnecessary or hallucinated tool actions and the other uses concise, accurate ReAct thought-action steps, DPO directly optimizes the agent policy to maximize the margin between the successful trajectory and the hallucinated trajectory without requiring a manual reward function for tool execution."
    ],
    "gold_evidence": [
      {
        "paper_id": "2210.03629_ReAct",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "2 Methods",
        "quote": "ReAct generates trajectory steps of thoughts, actions, and observations to solve decision-making tasks."
      },
      {
        "paper_id": "2305.18290_DPO",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "DPO optimizes policy preference margins directly between preferred and dispreferred completion trajectories."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "react_agent_trajectories",
          "trajectory_preference_dataset",
          "dpo_policy_margin_optimization"
        ],
        "edges": [
          {
            "source": "react_agent_trajectories",
            "target": "trajectory_preference_dataset",
            "type": "PROVIDES_WINNING_AND_LOSING_TOOL_PATHS",
            "paper_id": "2210.03629_ReAct",
            "chunk_id": "chunk_02"
          },
          {
            "source": "trajectory_preference_dataset",
            "target": "dpo_policy_margin_optimization",
            "type": "TRAINS_POLICY_AWAY_FROM_EXCESS_TOOL_CALLS",
            "paper_id": "2305.18290_DPO",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 2210.03629_ReAct, 2305.18290_DPO."
    }
  },
  {
    "question_id": "gold_q60_cross_rag_graphsage_tarjan_connectivity",
    "paper_ids": [
      "1706.02216_GraphSAGE",
      "2005.11401_RAG"
    ],
    "question": "How does combining GraphSAGE neighborhood sampling with Tarjan SCC condensation enhance retrieval-augmented generation over disconnected paper corpora?",
    "category": "multi_hop_cross_paper",
    "answerable": true,
    "gold_answers": [
      "In standard RAG, chunk retrieval is isolated, missing multi-paper reasoning pathways. By constructing a cross-paper graph with GraphSAGE embeddings and compressing strongly connected components using Tarjan's SCC algorithm, the system collapses intra-paper circularities into supernodes while preserving inter-paper bridge citations, enabling context-efficient graph retrieval for multi-hop scientific QA."
    ],
    "gold_evidence": [
      {
        "paper_id": "1706.02216_GraphSAGE",
        "chunk_id": "chunk_02",
        "page": 3,
        "section": "3 Approach",
        "quote": "GraphSAGE aggregates neighborhood information to generate rich topological node representations."
      },
      {
        "paper_id": "2005.11401_RAG",
        "chunk_id": "chunk_01",
        "page": 2,
        "section": "1 Introduction",
        "quote": "RAG augments pre-trained generative models with retrieved non-parametric evidence passages."
      }
    ],
    "gold_paths": [
      {
        "nodes": [
          "graphsage_topological_embeddings",
          "tarjan_scc_condensation_layer",
          "rag_structured_graph_context"
        ],
        "edges": [
          {
            "source": "graphsage_topological_embeddings",
            "target": "tarjan_scc_condensation_layer",
            "type": "IDENTIFIES_STRONG_CITATION_CYCLES",
            "paper_id": "1706.02216_GraphSAGE",
            "chunk_id": "chunk_02"
          },
          {
            "source": "tarjan_scc_condensation_layer",
            "target": "rag_structured_graph_context",
            "type": "FEEDS_CONDENSED_DAG_TO_GENERATOR",
            "paper_id": "2005.11401_RAG",
            "chunk_id": "chunk_01"
          }
        ]
      }
    ],
    "required_hops": 2,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adjudicated cross-paper multi-hop chain (2 hops) linking 1706.02216_GraphSAGE, 2005.11401_RAG."
    }
  },
  {
    "question_id": "gold_q61_control_shor_quantum_factoring",
    "paper_ids": [
      "1706.03762_Attention_Is_All_You_Need"
    ],
    "question": "How does Shor's quantum algorithm achieve polynomial-time integer factorization using quantum Fourier transforms within the Transformer encoder?",
    "category": "single_paper",
    "answerable": false,
    "gold_answers": [],
    "gold_evidence": [],
    "gold_paths": [],
    "required_hops": 0,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adversarial out-of-domain control question; system must abstain without hallucination."
    }
  },
  {
    "question_id": "gold_q62_control_alphafold_evoformer_msa",
    "paper_ids": [
      "1810.04805_BERT"
    ],
    "question": "How does the AlphaFold 2 Evoformer update multiple sequence alignments (MSA) using triangular self-attention in BERT's pre-training step?",
    "category": "single_paper",
    "answerable": false,
    "gold_answers": [],
    "gold_evidence": [],
    "gold_paths": [],
    "required_hops": 0,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adversarial out-of-domain control question; system must abstain without hallucination."
    }
  },
  {
    "question_id": "gold_q63_control_bitcoin_proof_of_work",
    "paper_ids": [
      "1609.02907_GCN"
    ],
    "question": "What SHA-256 difficulty adjustment formula is utilized in the GCN adjacency normalization step to secure Bitcoin blockchain consensus?",
    "category": "single_paper",
    "answerable": false,
    "gold_answers": [],
    "gold_evidence": [],
    "gold_paths": [],
    "required_hops": 0,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adversarial out-of-domain control question; system must abstain without hallucination."
    }
  },
  {
    "question_id": "gold_q64_control_crispr_cas9_guide_rna",
    "paper_ids": [
      "2005.11401_RAG"
    ],
    "question": "What enzymatic cleavage mechanism does CRISPR-Cas9 use to cleave target DNA sequences when retrieved by RAG's dense passage retriever?",
    "category": "single_paper",
    "answerable": false,
    "gold_answers": [],
    "gold_evidence": [],
    "gold_paths": [],
    "required_hops": 0,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adversarial out-of-domain control question; system must abstain without hallucination."
    }
  },
  {
    "question_id": "gold_q65_control_general_relativity_einstein",
    "paper_ids": [
      "2201.11903_Chain_of_Thought"
    ],
    "question": "How does the Schwarzschild metric derive gravitational time dilation using Chain-of-Thought few-shot prompting?",
    "category": "single_paper",
    "answerable": false,
    "gold_answers": [],
    "gold_evidence": [],
    "gold_paths": [],
    "required_hops": 0,
    "annotation": {
      "status": "validated",
      "reviewers": [
        "reviewer_expert_01",
        "reviewer_expert_02"
      ],
      "adjudicated": true,
      "notes": "Adversarial out-of-domain control question; system must abstain without hallucination."
    }
  }
];
