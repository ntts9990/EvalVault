Improving RAGAS Evaluation with Representative Sampling and Human Feedback

Introduction

RAGAS (Retrieval-Augmented Generation Assessment Suite) is an open-source framework for evaluating Q&A or retrieval-augmented generation systems. It provides metrics like Faithfulness, Answer Relevance, Context Precision, Context Recall, etc., often using an LLM “judge” to score how well an answer uses retrieved context and answers the question ￼ ￼. The goal is to measure if a model’s answer is grounded in provided knowledge or hallucinated ￼. In theory, such automated metrics should reflect aspects of user satisfaction (e.g. factual correctness and relevance contribute to user satisfaction) ￼. However, practitioners have reported that RAGAS scores do not always align with actual user satisfaction or answer quality ￼ ￼. In fact, RAGAS evaluations can be unstable (varying from run to run) and sometimes assign low scores even to correct answers ￼. There is also a lack of published validation showing strong correlation between RAGAS metrics and real user preferences ￼. These limitations make it hard to trust RAGAS scores as a sole indicator of answer quality or user happiness.

User Scenario: You have implemented a web UI that computes RAGAS scores and analyses for a dataset of Q&A pairs (or user queries and AI-generated answers). You observed that the RAGAS evaluation score often does not reflect user satisfaction well, and stakeholders are skeptical of the automated scores. Manually evaluating every Q&A in the entire dataset is impractical for users. To address this, you proposed a human-in-the-loop approach: use data clustering to pick a small set of representative questions/answers, have human evaluators (or end-users) rate those samples for satisfaction, then train a model using this human-labeled subset to predict satisfaction for all Q&As. This approach aims to calibrate or adjust the automated metric using real user feedback, yielding more trustworthy results.

Objective: This report examines from a machine learning engineering perspective how to implement this idea in detail and whether it is likely to be effective. We will outline a concrete methodology (including data selection, clustering, model training, etc.), and evaluate its feasibility and expected benefits using scientific evidence. We also consider incorporating additional data (e.g. multi-turn context or intermediate results) to improve accuracy. The goal is to determine if this human-in-the-loop calibration can realistically produce more accurate, user-aligned evaluation scores that stakeholders can trust.

Limitations of RAGAS and Motivation for Human Feedback

RAGAS provides a variety of metrics for RAG system performance, and being LLM-based, these metrics were intended to be “closer to human evaluation” than naive string overlap measures ￼ ￼. However, in practice several issues have been noted:
	•	Unreliability and Variance: RAGAS metrics can be non-deterministic (since they rely on LLM judgments) and may produce inconsistent results on the same data ￼ ￼. Users on the LangChain forum reported that RAGAS scores “differ heavily from run to run” and sometimes give zero or NaN scores even for correct answers ￼ ￼. Such instability undermines confidence in the scores.
	•	Poor Correlation with User Judgment: There is no strong evidence yet that RAGAS scores correlate with real user satisfaction or quality judgments ￼. One comment noted “no proper technical report or experiment that RAGAS is useful and effective to evaluate LLM performance”, suggesting caution in relying solely on these metrics ￼. In fact, the need for manual annotation is emphasized by users: one practitioner remarked that “the manual annotation seems really useful” in addition to automated metrics ￼. This implies that human evaluation may catch nuances that RAGAS misses.
	•	Narrow Focus of Metrics: RAGAS focuses on correctness and grounding (factuality) aspects ￼, which are critical but not the only determinants of user satisfaction. User satisfaction also depends on answer completeness, clarity, tone, helpfulness, etc., which an automated metric might not fully capture. For example, an answer could be factually correct (high RAGAS faithfulness) but written in a convoluted or unsympathetic manner, leading to low user satisfaction. RAGAS currently doesn’t measure qualities like tone or user-perceived helpfulness directly ￼.
	•	Thresholding and Interpretation: Even if RAGAS yields numeric scores, defining what score is “good enough” for users is tricky. Teams struggle to set thresholds for production or know how RAGAS translates to user happiness ￼. A Medium article noted that teams may struggle to correlate scores with actual user satisfaction and that “RAGAS also falls short” in guiding product readiness ￼ (suggesting RAGAS alone isn’t a reliable proxy for user experience). If high RAGAS scores don’t consistently mean users are happy (or low scores don’t always mean dissatisfaction), the metric loses practical value.

These factors motivate adding a human-in-the-loop calibration. By obtaining direct user evaluations on a subset of outputs, we get a ground truth for satisfaction against which we can adjust or learn a better mapping from RAGAS (and other features) to what users actually care about. This approach acknowledges that “evaluating LLM generation performance is not an easy problem and no silver bullet exists; mixing various metrics and human feedback is needed for reliable results” ￼.

Importantly, if we find instances where RAGAS gives a high score but humans are dissatisfied, it indicates a blind spot in the evaluation. Research on LLM evaluation suggests that “a mismatch between high metric scores and low user satisfaction indicates the evaluation dataset is not representative” of real usage ￼ ￼. In other words, solely relying on an automated metric can miss critical cases. Incorporating user feedback helps ensure the evaluation aligns with actual user experience.

Conclusion: There is a strong rationale to involve human judgments to calibrate or supplement RAGAS. The next sections describe a concrete plan to do so: selecting a representative subset of Q&A data, gathering user satisfaction ratings on them, and training a model to generalize these ratings across the full dataset. This plan essentially implements a form of active learning or human-in-the-loop model tuning to bridge the gap between RAGAS’s automated scores and true user satisfaction.

Overview of the Proposed Solution

The core idea is to use representative sampling + human feedback + model learning to improve evaluation. In summary, the workflow is:
	1.	Select Representative Q&A Samples: Using clustering or similar methods on the entire dataset of Q&A pairs (with their RAGAS scores and possibly text embeddings), identify a manageable subset of instances that are most informative and cover the diversity of the dataset. These will serve as “대표 문항” (representative items) for human evaluation, ensuring we don’t ask humans to rate dozens of near-duplicate questions. This tackles the issue that users cannot feasibly rate every data point.
	2.	Human Satisfaction Evaluation: Present the selected representative questions and their AI-generated answers (with any necessary context) to human evaluators (could be domain experts, end-users, or annotators via the web UI you built). Have them rate each answer’s quality or their satisfaction with it. This could be a numeric rating (e.g. 1–5 stars, or a percentage) or a categorical judgment (e.g. Satisfied/Neutral/Unsatisfied). The key is to capture the human’s overall satisfaction, taking into account all factors (correctness, usefulness, clarity, etc.). These human ratings become our ground truth labels for model training.
	3.	Feature Aggregation: For each evaluated sample, gather relevant features that could predict satisfaction. This includes the RAGAS metric outputs (faithfulness score, relevance score, etc., and any aggregate RAGAS score if available). Additionally, include textual or metadata features from the Q&A pair:
	•	The question text (possibly encoded as embeddings or analyzed for complexity),
	•	The answer text (e.g. length, presence of direct answer vs. fluff, sentiment/tone, etc.),
	•	Possibly semantic similarity between question and answer (using an embedding model to see if the answer is on-topic),
	•	If the interaction is multi-turn, include conversation context or multi-turn RAGAS metrics (RAGAS supports multi-turn evaluations ￼ ￼; features like whether the conversation achieved the user’s goal could be relevant).
	•	Any existing integrated scores (the question mentions “통합 분석 축 점수”, which sounds like a combined analysis score – that can be one feature).
By combining RAGAS’s structured metrics with NLP-based features of the content, we give our model a rich basis to learn from. Including data from multiple “points” or perspectives (e.g. both the score and the textual content, or multiple turns of the dialogue) should improve accuracy, as the model can catch nuances that a single score cannot ￼ ￼.
	4.	Train a Satisfaction Prediction Model: Using the labeled subset (with human satisfaction scores as target and the above features as inputs), train a machine learning model to predict user satisfaction for a given Q&A pair. This model will effectively learn the relationship between RAGAS metrics/text features and actual human satisfaction. Possible modeling approaches:
	•	A regression model (if satisfaction is numeric) or a classification model (if using categories like Good/Bad) such as XGBoost or Random Forest, which can handle mixed numeric and categorical features and is interpretable in terms of feature importance.
	•	A simple linear regression or logistic regression might suffice if we suspect a linear combination of metrics correlates with satisfaction (e.g. perhaps “Answer Relevance” is twice as important as “Context Precision”, etc., the model will learn such weights).
	•	If more advanced, one could fine-tune an LLM or a BERT-based model on this data, feeding the question + answer (and context) as input and the human score as output. However, given the likely small size of labeled data, a simpler model with engineered features is more practical and avoids overfitting.
During training, we should use techniques like cross-validation (especially since the labeled set may be small) to ensure the model generalizes and we’re not just fitting noise. The model’s performance can be evaluated by how well it predicts the human ratings on a held-out portion of the labeled data (e.g. measured by correlation or accuracy between model predictions and human scores).
	5.	Apply Model to Full Dataset: Once validated, deploy the trained model to predict satisfaction scores for all Q&A pairs in the dataset. For each item, input its features (RAGAS metrics, etc.) into the model to get a calibrated satisfaction estimate. These estimates are expected to be more aligned with actual user opinion than the raw RAGAS score. Essentially, we are using the model to “fill in” human judgment for the many items that were not manually rated, basing on patterns learned from those that were.
	6.	Integrate into UI and Iterate: The newly predicted satisfaction scores can be integrated back into your web UI or reporting system. This might involve displaying them as an adjusted score or using them to flag potentially low-satisfaction answers. It’s wise to also incorporate an iteration loop: if stakeholders still spot outputs where the score seems off, those could be added as new samples for human evaluation in a next round. Over time, this iterative labeling (an active learning approach) and model retraining will strengthen the evaluation. In active learning terms, we might choose additional samples where the model is most uncertain or where RAGAS and the model disagree (indicating confusion) to label next. This ensures we continually target the most informative data for human review.

The above approach embodies a human-aligned evaluation strategy. By focusing human effort on a small but representative set and letting the model generalize, we drastically reduce manual workload while still grounding the evaluation in reality. The next sections detail each step and the technical methods to implement them, followed by a discussion of feasibility and evidence for effectiveness.

Step 1: Selecting Representative Data via Clustering

To effectively choose a subset of Q&A pairs for human rating, we want those samples to be maximally informative and cover the spectrum of cases in the full dataset. Random sampling might miss edge cases or yield many similar items, so we use a more principled approach: clustering.

Data Preparation: First, we need to represent each Q&A pair in a form suitable for clustering. Options:
	•	Compute an embedding for each question-answer pair. For instance, use a sentence transformer or LLM to get a vector encoding the combined “question + answer” (perhaps also including retrieved context if applicable). Alternatively, create a concatenation of the question embedding and answer embedding. This vector should capture semantic content and some notion of answer quality.
	•	Include the RAGAS metric scores in the feature vector (e.g. append the numeric scores for faithfulness, relevance, etc., to the embedding). This way, the distance between two samples in feature space can reflect not just topical similarity but also similarity in how well the answers scored on the metrics. For example, one cluster might naturally form around items with low faithfulness scores (hallucinations), another with high scores but varying relevance, etc.

Clustering Algorithm: Use a clustering algorithm like K-Means or Hierarchical clustering on these feature vectors. The choice of number of clusters K depends on how many samples you can feasibly label – for example, if you can label ~50 items, you might choose K ≈ 50 clusters to get roughly one representative from each cluster. If you can label more, increase K accordingly.
	•	K-Means will partition the data into K clusters by minimizing intra-cluster variance. After clustering, we can select the centroid (or a point closest to the centroid) of each cluster as the representative. The centroid represents a “typical” example of that cluster. This avoids picking outliers and ensures coverage of distinct regions of the data distribution.
	•	An alternative is diversity sampling: use methods like K-Medoids or K-Center Greedy, which explicitly select a set of points that maximize coverage of the whole dataset’s diversity. The effect is similar to clustering – you end up with a set of well-spread examples.

Benefit: Clustering ensures we avoid redundancy in the labeled set. We don’t waste human effort labeling many similar questions that the model answered similarly. Instead, we label one example from each cluster of similar cases ￼. Research in active learning supports this approach: selecting the most representative samples from clusters yields better coverage and avoids repeatedly labeling points with essentially the same information ￼. This way, if the dataset has (for instance) a hundred questions about the same topic all answered incorrectly due to a certain flaw, clustering will group them and picking one or two from that cluster will inform the model about that entire scenario.

Distance Metrics: We should be mindful of how we measure similarity in clustering. Using cosine distance on embeddings is common for textual data. If RAGAS scores are included, they should be scaled appropriately (e.g. if embeddings are unit vectors and scores range 0–1, maybe give them some weight or normalize them) so they influence clustering. We might even cluster primarily by content and use metrics for sub-clustering or vice versa. This is a design choice – if the primary goal is to capture different kinds of model errors, then clustering by a mixture of content and metric scores is reasonable. For example, all items with low faithfulness might cluster together (hallucination cluster), items with perfect scores another (probably easy factual questions), etc. Ensuring diverse clusters means we’ll likely get some examples of all these situations in the representative set.

Choosing Cluster Representatives: After clustering, for each cluster we can choose:
	•	The item closest to the centroid (in vector distance). This is a straightforward representative.
	•	Optionally, the most extreme item if we specifically want a worst-case example from that cluster (e.g. lowest scoring item in that cluster) – but generally centroid gives a mid representative.
We should double-check that the chosen items indeed look diverse and cover different problems or topics. If some clusters seem too large or too heterogeneous (indicating maybe K was too small), we could increase K or manually ensure important distinct cases are separate.

Finally, compile the list of representative Q&A pairs. This list will be given to human evaluators in the next step. It’s good to randomize the order or group them logically so that a human reviewing doesn’t get bored by similar ones in a row (since we intentionally picked diverse ones, they shouldn’t be too similar anyway).

Note: If the dataset is truly large (thousands of items), one could do clustering in stages (hierarchical or coarse clustering to break into chunks, then finer clustering) or use a pre-clustering + active selection approach ￼ ￼. But given the plan is to label a relatively limited number, a single K-Means on embeddings is a reasonable approach for implementation simplicity.

Step 2: Human Evaluation of Selected Samples

With the representative set of Q&A pairs chosen, we move to human evaluation. The aim is to get a ground truth satisfaction score for each representative item, reflecting how a user would rate the answer’s quality. Here’s how to implement this step:
	•	Web UI or Annotation Platform: You mentioned having a web UI for RAGAS evaluation and analysis. This UI can be adapted or used to present questions and answers to evaluators. Alternatively, exporting the items to a spreadsheet or using a survey tool could work. The UI should display:
	•	The user’s question (or prompt).
	•	The AI’s answer.
	•	Optionally, any retrieved context or reference (since knowing what information was available might affect judgement of faithfulness – but if we assume the user only sees the answer, maybe we judge from user perspective which often doesn’t see context). This depends on whether we want the evaluator to judge factual correctness (they might need to know the truth) or just their satisfaction as a naive user. Often, user satisfaction is judged without seeing the retrievals, focusing on whether the answer seems correct and useful.
	•	A form input for the rating. For consistency, it’s good to define a clear rating scheme:
	•	e.g. 5-point Likert scale: 5 = Very satisfied (excellent answer), 1 = Very dissatisfied (poor answer), etc.
	•	Or a letter grade, or simply Good/Bad. A finer scale captures nuance but requires more judgment consistency; a coarser scale is easier but less informative. A 3-level (Good/Okay/Poor) could be a balanced choice as well.
	•	Possibly a text box for comments (optional, but might yield insights on why an answer is bad – useful for debugging model issues, though not strictly needed for training).
	•	Evaluation Criteria: We should instruct the human evaluators on what satisfaction means in this context. For example: “Rate how satisfied you are with the answer. Consider: Is it factually correct? Does it fully answer the question? Is it clear and easy to understand? Is the tone appropriate? Would you be satisfied if this were the answer you got as a user?” This ensures a consistent understanding. Since RAGAS metrics already check factuality and relevance, the human can implicitly cover those plus any additional factors like coherence and helpfulness.
	•	Who are the Evaluators: Ideally, people representative of end-users should do the rating. In some cases, domain experts are needed (e.g. if questions are highly specialized, we need knowledgeable raters to know if the answer is correct). If it’s general knowledge, crowd-sourced annotators could work, but then ensure they have access to verify facts if needed (like via web search) or provide the ground truth if available.
	•	Rating Process: The selected items could be rated by multiple humans to ensure reliability. If resources allow, having at least 2 independent ratings per item and then averaging them (or discussing disagreements) is ideal to reduce individual bias. If only one per item is feasible (perhaps if internal team is doing it), then we accept that but be aware of subjective bias. The web UI could allow the user (stakeholder) themselves to rate interactively, or you might organize a small evaluation session with colleagues.
	•	Collect Data: After evaluation, we will have a set of data points: for each representative Q&A, a human satisfaction score (or label). We should compile these into a structured format (e.g. a CSV with columns: question_id, question_text, answer_text, human_score, and also include the RAGAS metrics for that item).
	•	Optional – Validate Inter-Rater Agreement: If multiple people rated, compute agreement (Cohen’s kappa or just see if scores differ by more than 1 on a 5-point scale frequently). If inconsistency is high, clarify guidelines or have a discussion to calibrate the evaluators and maybe re-label some items. Consistent human data is important for training a good model.

By the end of this step, we have our training dataset: a small but representatively chosen set of Q&A instances with reliable human satisfaction judgments. This is essentially the “golden dataset” for our evaluation model, similar to how some evaluation frameworks encourage building a human-annotated golden set for calibration ￼ ￼.

It’s worth noting that the human ratings themselves could reveal interesting things: for example, we might find patterns like “RAGAS gave this item a high score but humans gave it a low rating” (those are the cases we specifically wanted to catch). Such insights can directly inform improvements (maybe the prompt or the retrieval strategy needs fixing for those cases). But primarily, these labels will feed into the modeling phase.

Step 3: Training a Satisfaction Prediction Model

Now comes the machine learning component: using the human-labeled subset to train a model that can predict user satisfaction for any Q&A pair in the dataset. Essentially, we treat it as a supervised learning problem where: inputs = various features of the Q&A (including RAGAS metrics), target = human satisfaction score.

Feature Engineering: We need to decide what features to give the model. Likely candidates include:
	•	RAGAS Metric Scores: For each item, we have metric outputs such as faithfulness_score, answer_relevance, context_precision, etc. These are numeric (often 0–1). RAGAS might also produce an overall score or allow weighting metrics into one; but it’s better to give the model the raw components so it can learn which aspects matter. For instance, the model might learn that Answer Relevance is strongly predictive of satisfaction (because if an answer isn’t relevant, user will be unhappy), whereas Context Recall might matter less to user satisfaction directly. Including all metrics allows the model to discover the best combination to match human ratings. (This is akin to learning a weighted metric that correlates with satisfaction.)
	•	Question & Answer Text Features: RAGAS’s LLM-based scores already encapsulate some text analysis, but we can add more:
	•	Use a language model embedding of the answer text as features, or simpler text features like answer length, number of sentences, etc. For example, extremely short answers might correlate with dissatisfaction if they seem non-informative, or overly long rambling answers might also lower satisfaction.
	•	Lexical or semantic overlap between question and answer: e.g., compute an embedding for the question and answer separately and measure cosine similarity. If an answer is off-topic, this similarity will be low and likely user satisfaction is low. RAGAS’s Answer Relevance metric probably does something similar internally, but an independent calculation could reinforce it.
	•	Readability or Tone: Possibly measure sentiment or politeness of the answer. A very negative or rude tone can hurt satisfaction. This may be less common, but a quick sentiment analysis or toxicity check could be included as binary features (e.g., “flag_toxic=1 if answer contains swear words or insults”).
	•	Answer Correctness vs Ground Truth: If a ground truth answer is available for these questions (sometimes in RAG setups you might have a known correct answer for evaluation), you can include a similarity score to the ground truth. RAGAS’s Answer Similarity metric (if enabled) does this ￼. If not already included, you could compute ROUGE or embedding similarity to the reference answer as a feature. This directly indicates factual correctness.
	•	Metadata: If available, any metadata like question category or difficulty could be features. For example, maybe user satisfaction tends to be lower on very hard questions (the model might struggle more). Including a category or topic might help the model calibrate (though clustering already tried to cover variety).
	•	Multi-turn/Time-series data (if applicable): If each Q&A is part of a multi-turn conversation, you could include features like number of turns used, whether the user had to rephrase the question (indicating initial answer was unsatisfactory), etc. RAGAS has multi-turn metrics like AgentGoalAccuracy or others for multi-turn interactions ￼. These could be included if relevant. The user’s question snippet mentioned “시계열 데이터 (time-series data) and multiple time points”, which suggests that considering how the conversation unfolds over time may help. For example, if a user asked a follow-up question, that implies the first answer wasn’t fully satisfying. If we had logs of user behavior (like if they clicked “thumbs down” or asked a new question), those signals of dissatisfaction could be integrated too. However, this goes beyond static Q&A pairs and into dynamic user interaction data. If available, it’s extremely useful to include (as implicit satisfaction feedback).

In summary, the feature vector for each data point could be: [faithfulness_score, answer_relevance, context_precision, context_recall, answer_similarity, answer_length, question_answer_similarity, sentiment_score, ...]. We will have such vectors for each item that was human-rated.

Model Choice: Given the likely small size of labeled data (maybe tens or hundreds of examples), a simple model is preferable:
	•	Tree-based models (Random Forest, XGBoost): handle nonlinear interactions and are robust with small data if not too many features. They can also give feature importance, which is informative (e.g. we might learn which RAGAS metric is most strongly tied to satisfaction).
	•	Linear models (Linear Regression or Logistic Regression): might work if the relationship is mostly linear. They are interpretable (coefficients showing how each feature contributes). We could start with a linear model as a baseline (like a weighted sum of metrics) and see performance.
	•	Neural networks: Not recommended unless the dataset of labels is larger. However, a pre-trained neural model (like fine-tuning a BERT on this regression) could leverage transfer learning from language understanding. If we had a few hundred labeled items, fine-tuning a small LLM or a RoBERTa on the task “predict satisfaction from [question; answer]” could be attempted. This would inherently use the text, but we’d lose the explicit use of RAGAS metrics. One hybrid approach could be feeding the metrics as part of the input text (e.g. a prompt: “Question: X; Answer: Y; Metrics: (F=0.8,R=0.7,…) – predict satisfaction”). This is quite complex though and likely overkill. A structured model is simpler and sufficient.

We also decide on output format:
	•	If using numeric satisfaction (like 1–5 rating), we can treat it as regression (predict a continuous score). We should then round or bucket the predictions if needed when presenting (or keep them continuous if that’s fine).
	•	If categories, treat as classification (e.g. a 3-class classifier for Good/Okay/Bad). Classification might be easier if humans gave coarse labels.

Training Process:
	•	Split the labeled data into training and validation (for example 80% train, 20% held-out). If the labeled set is very small (e.g. <50), use cross-validation (e.g. 5-fold CV) to reliably estimate performance.
	•	Train the model on the training portion. Optimize hyperparameters if needed (though for something like XGBoost, default parameters might be okay, or we can do a small grid search).
	•	Evaluate on validation: see how well the model’s predictions agree with human scores. For regression, compute mean squared error and maybe correlation (Pearson’s r or Spearman) between predicted and actual ratings. For classification, compute accuracy and perhaps weighted F1 if class imbalance.
	•	If performance is unsatisfactory (e.g. the model isn’t much better than just using RAGAS score alone), investigate:
	•	Check if features are insufficient (maybe add more features or try a more complex model).
	•	Check if data quality is an issue (noisy labels).
	•	Possibly the relationship is complex – at this point, a quick check could be to see correlation of individual RAGAS metrics with human scores. If none correlate at all, either humans rated on factors entirely orthogonal to RAGAS, or RAGAS indeed fails badly; then a text-based model might be needed to capture it. But likely, metrics like answer relevance will correlate somewhat with satisfaction.
	•	One might also try a simple baseline: e.g. does a single RAGAS metric or the average of metrics correlate with human scores? If correlation is e.g. 0.2 but our model achieves 0.6, that’s a good improvement, demonstrating the calibration worked.

Outcome: We expect this model to learn a function that more closely mimics human judgment. For example, it might learn to down-weight faithfulness if it finds that even some answers that stray from context weren’t penalized by humans as much as being relevant. Or it might learn to heavily weight answer relevance and correctness. Essentially, it’s like creating a custom weighted metric tuned to what users consider a good answer. In similar fashion, AI evaluation research sometimes trains metrics to better correlate with human judgments ￼ (for instance in machine translation, metrics like BLEURT or COMET are learned to match human scores).

One could consider this model a kind of “reward model” if you draw analogy to reinforcement learning from human feedback (RLHF): there, a reward model is trained on human preference data to predict what humans would prefer. Here, our predictor of satisfaction is exactly that kind of model (though we aren’t necessarily using it for RL, just evaluation). Notably, OpenAI’s InstructGPT work showed that using a model trained on human preferences made the system outputs align much better with what users want ￼ ￼. While our use-case is evaluation rather than generation, it’s the same principle: training on human feedback leads to outputs (in this case, scores) that better reflect human perspectives. InstructGPT’s smaller model fine-tuned with human feedback even outperformed a much larger model in user ratings ￼ ￼, reinforcing that human-aligned signals drastically improve quality as perceived by users. This is strong evidence that our approach – incorporating human labels to adjust the metric – can be effective in producing results that humans agree with.

Step 4: Deploying the Calibrated Evaluation Model

After training, we have a validated model that can predict user satisfaction for Q&A pairs. The final step is to apply this model to the remaining (unlabeled) items in the dataset and integrate the results into your workflow.

Scoring the Full Dataset: For each Q&A pair in the entire dataset (except those we used for training, which we already have human scores for), do the following:
	•	Compute the same set of features we defined earlier (RAGAS metrics for that pair, textual features, etc.). Since you likely already have RAGAS metrics computed (via your UI or offline), you can reuse those. Ensure any new item is processed the same way as training items (for example, if we need an embedding for the answer, compute it using the same model we used before).
	•	Feed the features into the trained prediction model to get a predicted satisfaction score or label.

This will give each Q&A a new score, which we can call something like “Predicted User Satisfaction” or “Calibrated Score”. For interpretability, you might map numeric outputs into categories (e.g. if the model predicts 0.8 on a 0-1 scale, maybe call it “High satisfaction”). But it may be fine to keep the numeric value especially if using regression.

Integration into UI: In the web UI you built for evaluation, these new scores can be presented. For example:
	•	Next to the original RAGAS scores, you could display the human-calibrated score. This shows users or stakeholders an estimate of satisfaction. They might trust this more because they know it’s at least partially based on real human input.
	•	You could allow sorting or filtering by this score to identify answers likely to be problematic. For instance, find all Q&As with low predicted satisfaction (even if RAGAS might have been high). Those could be reviewed manually or flagged for improvement.
	•	Also, the representative examples that were human-rated – you can highlight those as “benchmarks” in the UI, possibly showing the actual human rating for those to give context.

Monitoring and Maintenance: The deployment doesn’t end with one training. Over time, you should monitor how well these predictions align with reality:
	•	If you have an ongoing user feedback mechanism (say the web UI allows users to give a thumbs-up/down on answers in practice), those can be collected to further validate the model’s accuracy on real usage.
	•	As the system (or underlying AI model) changes, the evaluation model might need retraining. For example, if you improve the QA system, the distribution of errors changes, so the representative set might need updating or the model retrained with new human labels focusing on new errors.

Incorporating New Data: The initial clustering and labeling was a one-time process, but it can be repeated periodically:
	•	After deploying, maybe you find a cluster of errors that was not considered before. You can add a few examples of those to the labeled set and retrain.
	•	The evaluation approach should remain dynamic. As one paper suggests, the evaluation dataset should be “dynamic, treated as a living body that evolves as the application changes” ￼ ￼. This means our representative set and model should be updated when new types of queries or failures arise. The initial 50 or 100 samples might cover current usage, but if the domain of questions shifts, we’d gather new labels in those areas.

In summary, deployment involves using the model’s output as the new metric going forward. This doesn’t necessarily mean discarding RAGAS – in fact, RAGAS metrics remain useful diagnostics (e.g. they tell you if factual correctness is low, which is actionable). But the combined satisfaction score is what you would use for overall evaluation or for decision-making (like which answers need human review). It provides a single measure that more closely tracks what a user would think, thanks to the training we did.

Feasibility and Effectiveness Analysis

Implementability: The outlined solution is technically feasible with standard machine learning tools and does not require an unreasonable amount of data:
	•	Clustering embeddings for selection is computationally straightforward (even for thousands of points, k-means will finish quickly). Many libraries (scikit-learn, Faiss, etc.) can handle this.
	•	The human evaluation step is the most effort-intensive, but it’s manageable since we restricted the sample size. If, say, 50–100 items are chosen, a single evaluator can rate these in perhaps an hour or two, or spread across a few days. Using your web UI for this makes it user-friendly. Export/import via Excel as you mentioned is also workable if the UI can’t do the rating input directly.
	•	Training the satisfaction model is not computationally heavy given the small data (it could even be done in Excel with a regression add-on theoretically, but better to use Python/R). The features are mostly numeric or easily derivable. If needed, using an AutoML tool could even expedite finding a good model, but a manual approach with XGBoost or regression is quite sufficient here.
	•	The one complexity might be integrating the model’s prediction back into the system. But since you have a custom UI, you likely can modify it to call the model or to display precomputed scores. If the model is simple (e.g. linear combination of metrics), you could even implement it as a formula directly in the UI backend. If it’s a tree model, you might save it and run a small script to output scores which are then stored. Overall, integration should be doable.

Effectiveness Expectations: We anticipate that this human-calibrated metric will be more trustworthy and correlated with user satisfaction than the raw RAGAS scores, because it’s literally trained to do that. Some supporting arguments and evidence:
	•	Active Learning Literature: The approach of labeling a representative subset and training a model is essentially a form of active learning/human-in-the-loop evaluation. This method is widely used to maximize information gain from limited labels ￼. By labeling representative samples, we ensured our training data covers diverse conditions, which improves generalization to the rest of data. Active learning research shows that a clustering-based sampling can achieve better performance with fewer labels by avoiding redundant information ￼. Thus, we expect our model, trained on a smartly chosen subset, to perform well on the unlabeled examples.
	•	Alignment with Human Preferences: There is strong evidence that incorporating human feedback leads to systems that align better with human expectations. For example, reinforcement learning from human feedback (RLHF) was used by OpenAI to fine-tune GPT models; the result (InstructGPT) was preferred by users and more reliable than the base model ￼ ￼. While our case is about evaluation, not generating answers, the analogy holds: using human ratings to train a model improves alignment of that model’s outputs (here, the outputs are evaluation scores) with what humans actually think. In short, our metric will be human-aligned by design. We are effectively tackling the problem noted by one practitioner: “evaluating LLM performance is not easy and has no silver bullet; all we can do is experiments and mix metrics for reliable results” ￼. Our experiment is mixing an automated metric (RAGAS) with human feedback to get a reliable result.
	•	Detecting Hidden Issues: The new approach can catch issues that RAGAS might ignore. For instance, if users commonly find an answer unsatisfactory due to style or partial completeness, the human scores will reflect that, and the model can learn those signals (perhaps via answer length or other features) even if RAGAS metrics were blind to it. This addresses the earlier point that RAGAS focuses on limited aspects. Our calibrated model encompasses a broader notion of quality as taught by real user opinions.
	•	Quantitative Improvement: We expect a higher correlation between the calibrated scores and actual user satisfaction than between RAGAS and user satisfaction. If we had the capacity to do a user study, we could verify that. But anecdotal evidence from domain knowledge: It is known that automatic metrics often have only moderate correlation with human judgments (e.g., BLEU vs human in translation). By training on human judgments, metrics like BLEURT improved that correlation significantly ￼. We anticipate similarly that our learned metric will better predict user survey results. In fact, the Arxiv “Practical Guide” suggests correlating offline metrics with in-product user satisfaction surveys, and adjusting if there’s mismatch ￼ ￼. Our plan is essentially doing exactly that alignment.
	•	Trust and Interpretability: Because our model can be analyzed (especially if using interpretable models), we can provide reasoning to stakeholders for why a certain score is given. For example, “This answer got a low satisfaction score because it had low Answer Relevance and the answer was very short – factors which our model learned are associated with user dissatisfaction.” This kind of explanation can build trust in the metric. It transforms the evaluation from a black-box LLM judgment (which RAGAS uses under the hood) to a more transparent, data-driven metric grounded in user input.

Potential Challenges and Mitigations:
	•	Label Quality: If the human evaluation is rushed or inconsistent, the model will learn a noisy mapping. Mitigation: use clear guidelines and possibly multiple ratings per item to ensure quality labels. The sample size is small, so one can review each label for sense. If any label seems obviously wrong (maybe the human misunderstood the question), we can correct it.
	•	Model Overfitting: With a small training set, there’s risk the model overfits peculiarities of those examples. Mitigation: use cross-validation, limit model complexity (e.g. depth of trees), and evaluate carefully. Also, clustering selection helps because it avoids many nearly-duplicate points that could lead to overemphasis on one type of data.
	•	Coverage: It’s possible our representative set missed some rare scenario, thus the model might be clueless when encountering that scenario in unlabeled data. If such cases are important (e.g. a rare but critical failure mode), they should ideally be forced into the representative set initially or caught in a second iteration. Our approach is flexible: we can always add more samples (especially if we see the model performing poorly on some items, we can then get human labels for a few of those and update the model). This iterative improvement is a known best practice: “continuous evaluation and iterative refinement” are recommended so that evaluation suites mature with the system ￼ ￼.
	•	Scalability: If in the future the dataset grows or updates rapidly, one might not want to redo clustering from scratch each time. However, if the changes are incremental, one could classify new items by the existing model and maybe occasionally add a few new labels for new content areas. The approach scales in the sense that you usually don’t need to label a high percentage of data to maintain a good model – just enough to cover new ground.

Scientific Grounds for Efficacy:
To sum up the evidence:
	•	Using representative sampling ensures our human-labeled data is not biased or narrow, addressing the issue that an unrepresentative evaluation set can mislead metrics ￼ ￼.
	•	Active learning theory supports that labeling the most informative examples yields better learning with fewer labels ￼.
	•	Human feedback alignment (like RLHF) has empirically proven to improve alignment with user preferences in AI systems ￼ ￼.
	•	Community feedback on RAGAS highlights the gap we’re trying to fill – by bringing in human judgment, we answer the criticism that automated metrics alone are insufficient ￼. In fact, others have suggested mixing metrics or using alternatives like G-Eval; our approach can be seen as creating a custom metric tailored to our application and users.
	•	Outcome metrics vs user satisfaction: In production AI, it’s known that one should track user satisfaction explicitly as a metric (via surveys or feedback) because automated metrics are proxies ￼ ￼. Our solution effectively creates a predictive proxy for user satisfaction grounded in actual user input, which is a step closer to measuring what truly matters (the users’ experience).

Will this solution likely improve trust? Yes. By explaining that the new evaluation model is trained on our own users’ feedback (even if indirectly via a sample), stakeholders will inherently trust it more than a one-size-fits-all metric coming from an LLM’s judgment. It becomes a data-driven, customized evaluation metric. We can demonstrate its effectiveness by showing a few concrete examples: “Here is a question where RAGAS gave a high score but our users rated it poorly; our new model correctly predicts a low satisfaction for it.” Showing such examples will powerfully illustrate the value. Additionally, we can quantify improvements (e.g., “The correlation between our metric and user ratings improved from 0.3 to 0.8 after calibration”).

In conclusion, the idea of clustering to find representative questions, having humans rate them, and training a model on those ratings is not only practical to implement but also grounded in well-established practices (active learning, human-in-the-loop AI). It addresses the shortcomings of the RAGAS score by directly tying the evaluation to what users care about. The evidence from prior research and industry experience strongly suggests this approach will make the evaluation more accurate and more aligned with true user satisfaction. Therefore, the idea is very much feasible and likely to be effective.

Conclusion

We have outlined a detailed plan to enhance the RAGAS evaluation process with human feedback and machine learning, and examined its feasibility and effectiveness. By selecting a diverse subset of Q&A pairs via clustering, we ensure human reviewers only evaluate a manageable number of examples that capture the variety of the dataset. Those human satisfaction ratings provide the ground truth needed to train a calibration model that maps RAGAS metrics and other features to predicted user satisfaction. Deploying this model yields a new evaluation score for all items that is closely aligned with actual user judgments.

This approach effectively creates a customized metric that overcomes RAGAS’s limitations (such as instability and weak correlation to user happiness) by infusing it with real user-driven data. It is grounded in active learning principles and the success of human-in-the-loop training seen in other AI domains. We cited evidence that methods combining automated evaluation with human input result in more reliable performance assessment and improved alignment with user expectations ￼ ￼.

In practical terms, the implementation demands some upfront effort (clustering computation and a round of human rating), but these are well within the capacity of a small engineering team and can be streamlined with your existing UI tools. The payoff is a significant improvement in evaluation quality: stakeholders will be able to trust that the scores presented reflect what a user would actually feel, not just an abstract formula. This can guide better decision-making, model improvements, and user experience tuning.

Moreover, the solution is extensible – it sets up a framework for ongoing learning. As new data comes in or the system evolves, you can periodically update the representative set and retrain, thereby keeping the evaluation metric up-to-date with what users value. In a field where “no single metric is a silver bullet” ￼ ￼, this adaptive human-aligned approach offers a way to continually ground the evaluation in reality.

Final Assessment: Based on the analysis, your idea of leveraging representative human evaluations to calibrate the RAGAS score is both implementable and scientifically sound. It addresses a known gap (automatic metrics vs. user satisfaction) with a method that is supported by research and practice. We expect it will indeed yield more accurate and credible results. Adopting this approach can significantly improve confidence in the evaluation of your AI system’s answers, ultimately leading to a better alignment with user needs and a better user experience.

References:
	•	Srinivas Bommena, “A Practitioner’s Guide to Evaluating GenAI Applications with RAGAS,” Medium, 2025 – discusses RAGAS metrics and challenges ￼.
	•	Reddit discussion in r/LangChain, “Why is everyone using RAGAS for RAG evaluation? It looks very unreliable,” 2024 – reports on RAGAS score variability and lack of proven efficacy ￼ ￼.
	•	Ethan M. Rudd et al., “A Practical Guide for Evaluating LLMs and LLM-Reliant Systems,” arXiv 2506.13023, 2025 – emphasizes representative datasets and aligning metrics with user satisfaction (user surveys) ￼ ￼.
	•	Nguyen & Smeulders, “Active Learning Using Pre-clustering,” ICML 2004 – proposes selecting cluster representatives to maximize information and avoid redundant labeling ￼.
	•	OpenAI (Ouyang et al.), “Training Language Models to Follow Instructions with Human Feedback,” NeurIPS 2022 (InstructGPT paper) – demonstrated that models fine-tuned with human preference data produce outputs that users strongly prefer ￼.

## EvalVault 적용 설계 (한국어 문서 기준)

### 목표
- RAGAS 점수와 사용자 만족도 간 괴리를 줄이기 위해 대표 샘플 인간 평가 + 보정 모델을 EvalVault에 통합한다.
- 한국어 문서/질문 환경에 맞춘 피처와 프롬프트를 활용한다.
- CLI와 Web UI를 동시에 제공하며, 모든 데이터는 DB에 영속 저장한다.

### 핵심 결정 사항
- 만족도 라벨: 1~5 정수형
- Thumb 피드백: up/down/none (약한 레이블)
- 표기 방식: RAGAS 점수 옆에 보정 점수(`calibrated_satisfaction`) 병렬 표시
- 결측치 보정: 모델 예측값으로 보정하고 `imputed` 플래그 및 `imputation_source` 표시
- 모델: 선형회귀 + XGBoost 회귀 병행 (기본 출력은 XGBoost, 선형은 설명용)
- 다중 평가자 허용, 케이스 평균 및 run 평균 제공

### 데이터 모델 (권장)
- 테이블: `satisfaction_feedback`
  - `id` (PK)
  - `run_id`
  - `test_case_id`
  - `satisfaction_score` (1~5, nullable)
  - `thumb_feedback` (`up`/`down`/`none`)
  - `comment` (nullable)
  - `rater_id` (nullable)
  - `created_at`

- 케이스 결과 확장 (응답/저장 시 포함)
  - `calibrated_satisfaction` (float, 1~5)
  - `imputed` (bool)
  - `imputation_source` (`model`/`thumb`/`none`)

- run summary 확장
  - `avg_satisfaction_score` (라벨 있는 케이스 평균)
  - `thumb_up_rate`
  - `imputed_ratio` (보정 적용 비율)

### 저장/조회 전략 (SQLite + Postgres)
- StoragePort에 피드백 저장/조회 인터페이스 추가
- SQLite/Postgres 어댑터 모두에서 동일 스키마 지원
- 다중 평가자 허용, 케이스 단 평균은 조회 시 집계

### API 설계 (FastAPI)
- `POST /api/v1/runs/{run_id}/feedback`
  - 요청: `test_case_id`, `satisfaction_score?`, `thumb_feedback?`, `comment?`
- `GET /api/v1/runs/{run_id}/feedback`
  - 응답: 피드백 리스트
- `GET /api/v1/runs/{run_id}`
  - summary에 `avg_satisfaction_score`, `thumb_up_rate`, `imputed_ratio` 포함
  - results[].metrics에 `calibrated_satisfaction`, `imputed`, `imputation_source` 포함

### CLI 설계
- `evalvault calibrate --run-id <ID> [--model linear|xgb|both] [--write-back]`
- `--write-back` 시 보정 결과를 DB에 저장
- CLI 실행 결과로 모델 성능 요약(상관계수/MAE) 출력

### Web UI 설계 (RunDetails)
- 탭 추가: "만족도 평가"
  - 별점(1~5), thumb up/down, 코멘트 입력
  - 테스트 케이스별 저장 버튼
- Summary 카드 추가
  - 평균 만족도 점수, Thumb Up 비율, 보정 비율
- 메트릭 표에 `calibrated_satisfaction` 컬럼 추가 (RAGAS 옆 표시)
- 표시 옵션
  - 소수점 그대로 vs 정수 반올림 토글

### 보정(결측치 처리) 규칙
- `satisfaction_score` 없음 + `thumb_feedback` 있음 → 약한 레이블 매핑
  - `up = 4.0`, `down = 2.0`
- 둘 다 없으면 모델 예측값 사용
- 모든 예측값은 1~5 범위로 클리핑
- `imputed` 및 `imputation_source`를 반드시 표기

### 모델 피처 (한국어 최적화 포함)
- RAGAS 메트릭: faithfulness, answer_relevancy, context_precision, context_recall
- 한국어 피처
  - 답변 길이
  - 질문 키워드 누락률
  - 형태소 다양성(TTR)

### 운영/반복 개선
- 대표 샘플 재선정(클러스터링) → 주기적 라벨링 → 모델 재학습
- 불확실성 기반 샘플 추가(예측값 2.4~2.6 등 경계 구간)
- RAGAS 프롬프트 오버라이드와 한국어 평가 프롬프트 병행

### 구현 위치(예시)
- 모델/보정 로직: `src/evalvault/domain/services/satisfaction_model.py`
- 피드백 저장: `src/evalvault/adapters/outbound/storage/*_adapter.py`
- API 라우터: `src/evalvault/adapters/inbound/api/routers/runs.py`
- CLI: `src/evalvault/adapters/inbound/cli/commands/calibrate.py`
- UI: `frontend/src/pages/RunDetails.tsx`
