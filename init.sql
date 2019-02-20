BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS venues (id SERIAL PRIMARY KEY, name TEXT);
INSERT INTO "venues" (name) VALUES('Chipotle');
INSERT INTO "venues" (name) VALUES('Ni Marco''s');
INSERT INTO "venues" (name) VALUES('Cheba Hut');
INSERT INTO "venues" (name) VALUES('Fratelli''s');
INSERT INTO "venues" (name) VALUES('Beaver Street');
INSERT INTO "venues" (name) VALUES('Subway');
INSERT INTO "venues" (name) VALUES('Hot Wok');
INSERT INTO "venues" (name) VALUES('Crystal Creek');
INSERT INTO "venues" (name) VALUES('Wildflower');
INSERT INTO "venues" (name) VALUES('Pita Jungle');
INSERT INTO "venues" (name) VALUES('Picnic at Wheeler');
INSERT INTO "venues" (name) VALUES('Diablo Burger');
INSERT INTO "venues" (name) VALUES('Mix');
INSERT INTO "venues" (name) VALUES('Tacos Los Altos');
INSERT INTO "venues" (name) VALUES('Morning Glory Cafe');
INSERT INTO "venues" (name) VALUES('Ewa''s');
INSERT INTO "venues" (name) VALUES('The Creperie');
INSERT INTO "venues" (name) VALUES('Bigfoot BBQ');
INSERT INTO "venues" (name) VALUES('Dara Thai');
INSERT INTO "venues" (name) VALUES('Pato Thai');
INSERT INTO "venues" (name) VALUES('Pita Pit');
INSERT INTO "venues" (name) VALUES('Hiro''s Sushi');
INSERT INTO "venues" (name) VALUES('Oregano''s');
INSERT INTO "venues" (name) VALUES('Picazzo''s');
INSERT INTO "venues" (name) VALUES('Greek Islands');
INSERT INTO "venues" (name) VALUES('Macy''s');
INSERT INTO "venues" (name) VALUES('Lumberyard');
INSERT INTO "venues" (name) VALUES('Salsa Brava');
INSERT INTO "venues" (name) VALUES('El Capitan');
INSERT INTO "venues" (name) VALUES('Monsoon');
INSERT INTO "venues" (name) VALUES('Pizzicletta');
INSERT INTO "venues" (name) VALUES('Biff''s Bagels');
INSERT INTO "venues" (name) VALUES('Teppan Fuji');
INSERT INTO "venues" (name) VALUES('Olive Garden');
INSERT INTO "venues" (name) VALUES('Buffalo Wild Wings');
INSERT INTO "venues" (name) VALUES('Delhi Palace');
INSERT INTO "venues" (name) VALUES('Taverna');
INSERT INTO "venues" (name) VALUES('Cafe Rio Mexican Grill');
INSERT INTO "venues" (name) VALUES('Cafe Ole');
INSERT INTO "venues" (name) VALUES('Satchmo''s');
CREATE TABLE lunches (id SERIAL PRIMARY KEY, dayOfLunch DATE DEFAULT CURRENT_DATE, query TEXT, timeVotingEnds TIME DEFAULT '11:30');
CREATE TABLE votes (id SERIAL PRIMARY KEY, lunchId integer REFERENCES lunches ON DELETE CASCADE,
    creationDate DATE DEFAULT CURRENT_DATE,
    vote1 integer REFERENCES venues ON DELETE CASCADE,
    vote2 integer REFERENCES venues ON DELETE CASCADE,
    vote3 integer REFERENCES venues ON DELETE CASCADE);
COMMIT;
