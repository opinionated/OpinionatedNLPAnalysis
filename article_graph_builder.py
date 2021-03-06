import networkx as nx
import re

class Article:
	def __init__(self, name, data):
		self.name = re.sub(r'[^A-z0-9 ]', '', name)
		self.sentiment = 0
		self.emotions = {'anger': 0, 'joy': 0, 'fear': 0, 'sadness': 0, 'disgust': 0}
		self.taxonomies = {}
		self.entities = {}

		n = len(data)
		for sentence in data:
			self.addSentiment(sentence['docSentiment'], n)
			self.addEmotion(sentence['docEmotions'], n)

			for t in sentence['taxonomy']:
				for l in t['label'].split('/'):
					if l not in self.taxonomies:
						self.taxonomies[l] = 0
					self.taxonomies[l] = max(self.taxonomies[l], float(t['score']))

			words = sentence['entities']+sentence['keywords']
			for w in words:
				self.addEntity(w, n*len(words))

	def addEntity(self, w, n=1):
		weight = float(w['relevance'])
		self.addSentiment(w['sentiment'], n, weight)
		self.addEmotion(w['emotions'], n, weight)

		text = w['text'].lower()
		if text not in self.entities:
			self.entities[text] = 0
		self.entities[text] = max(self.entities[text], weight)

	def addSentiment(self, data, n=1, weight=1):
		if data['type'] != 'neutral':
			self.sentiment += weight*float(data['score'])/n

	def addEmotion(self, data, n=1, weight=1):
		for m in self.emotions:
			self.emotions[m] += weight*float(data[m])/n

def compareWords(words1, words2, threshold=0):
	set1 = set(words1)
	set2 = set(words2)

	matches = set1 & set2
	misses  = set1 ^ set2

	matchWeight = sum([words1[t]+1 for t in words1 if t in matches])
	missWeight  = sum([words1[t]+1 for t in words1 if t in misses ]) + sum([words2[t]+1 for t in words2 if t in misses])

	p = 1.0*matchWeight/(1+matchWeight+missWeight)
	if p > threshold:
		return p
	return 0

def compareSentiment(a1, a2, threshold=0):
	p = abs(a1.sentiment-a2.sentiment)
	if p > threshold:
		return p
	return 0

def compareEmotions(a1, a2, threshold=0):
	p = max([abs(a1.emotions[e] - a2.emotions[e]) for e in a1.emotions])
	if p > threshold:
		return p
	return 0

def addEdges(graph, articles):
	for i in range(len(articles)):
		graph.add_node(articles[i])
		for j in range(i+1, len(articles), 1):
			a1 = articles[i]
			a2 = articles[j]
			e = compareWords(a1.entities, a2.entities, 0.06)
			t = compareWords(a1.taxonomies, a2.taxonomies, 0.25)
			if e > 0 and t > 0:
				s = compareSentiment(a1, a2)
				m = compareEmotions(a1, a2)
				v = "similar"
				if s > 0.12 and m > 0.12:
					v = "opposing"
				graph.add_edge(a1,
					a2,
					viewpoint=v,
					entity_weight=e,
					taxonomy_weight=t,
					sentiment_weight=s,
					emotion_weight=m)

def build_article_graph_from_data(data):
	articles = []
	for article in data:
		articles.append(Article(article, data[article]))

	graph = nx.Graph()
	addEdges(graph, articles)

	for e in graph.edges(data=True):
		print e[0].name
		print e[1].name
		if 'entity_weight' in e[2]:
			print 'entity:', e[2]['entity_weight']
		if 'taxonomy_weight' in e[2]:
			print 'taxonomy:', e[2]['taxonomy_weight']
		if 'sentiment_weight' in e[2]:
			print 'sentiment:', e[2]['sentiment_weight']
		if 'emotion_weight' in e[2]:
			print 'emotion:', e[2]['emotion_weight']
		if 'viewpoint' in e[2]:
			print 'viewpoint:', e[2]['viewpoint']
		print
	return graph
