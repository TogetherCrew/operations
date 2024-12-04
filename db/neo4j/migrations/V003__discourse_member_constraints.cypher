CREATE CONSTRAINT FOR (obj:DiscoursePost) REQUIRE (obj.topicId, obj.endpoint, obj.postNumber) IS UNIQUE;
CREATE CONSTRAINT FOR (obj:DiscoursePost) REQUIRE (obj.id, obj.endpoint) IS UNIQUE;
CREATE CONSTRAINT FOR (obj:DiscourseTopic) REQUIRE (obj.id, obj.endpoint) IS UNIQUE;
CREATE CONSTRAINT FOR (obj:DiscourseUser) REQUIRE (obj.id, obj.endpoint) IS UNIQUE;
