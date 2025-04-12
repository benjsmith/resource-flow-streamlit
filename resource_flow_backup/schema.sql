CREATE TABLE allocation_id_map(old_id INTEGER, new_id VARCHAR);
CREATE TABLE demand_id_map(old_id INTEGER, new_id VARCHAR);
CREATE TABLE monthly_demand_allocation(year_month DATE, demand_fte FLOAT DEFAULT(0), allocation_fte FLOAT DEFAULT(0), capacity_fte FLOAT DEFAULT(0), PRIMARY KEY(year_month));
CREATE TABLE person_id_map(old_id INTEGER, new_id VARCHAR);
CREATE TABLE projects(id INTEGER PRIMARY KEY, "name" VARCHAR NOT NULL, description VARCHAR, start_date DATE NOT NULL, end_date DATE, status VARCHAR DEFAULT('planning'), project_manager_id INTEGER, project_type VARCHAR, lead_team_id INTEGER);
CREATE TABLE project_id_map(old_id INTEGER, new_id VARCHAR);
CREATE TABLE teams(id INTEGER PRIMARY KEY, "name" VARCHAR NOT NULL, description VARCHAR);
CREATE TABLE teams_uuid(id VARCHAR PRIMARY KEY, "name" VARCHAR NOT NULL, description VARCHAR);
CREATE TABLE team_id_map(old_id INTEGER, new_id VARCHAR);
CREATE TABLE people(id INTEGER PRIMARY KEY, "name" VARCHAR NOT NULL, "role" VARCHAR, skills VARCHAR, team_id INTEGER, FOREIGN KEY (team_id) REFERENCES teams(id));
CREATE TABLE people_uuid(id VARCHAR PRIMARY KEY, "name" VARCHAR NOT NULL, "role" VARCHAR, team_id VARCHAR, FOREIGN KEY (team_id) REFERENCES teams_uuid(id));
CREATE TABLE projects_uuid(id VARCHAR PRIMARY KEY, "name" VARCHAR NOT NULL, description VARCHAR, start_date DATE NOT NULL, end_date DATE, status VARCHAR DEFAULT('planning'), project_manager_id VARCHAR, project_type VARCHAR, lead_team_id VARCHAR, FOREIGN KEY (project_manager_id) REFERENCES people_uuid(id), FOREIGN KEY (lead_team_id) REFERENCES teams_uuid(id));
CREATE TABLE demands_uuid(id VARCHAR PRIMARY KEY, project_id VARCHAR NOT NULL, role_required VARCHAR, fte_required FLOAT NOT NULL, start_date DATE NOT NULL, end_date DATE NOT NULL, priority INTEGER DEFAULT(1), status VARCHAR DEFAULT('open'), FOREIGN KEY (project_id) REFERENCES projects_uuid(id));
CREATE TABLE allocations(id VARCHAR PRIMARY KEY, person_id VARCHAR NOT NULL, project_id VARCHAR NOT NULL, demand_id VARCHAR, fte_allocated FLOAT NOT NULL, start_date DATE NOT NULL, end_date DATE NOT NULL, notes VARCHAR, FOREIGN KEY (person_id) REFERENCES people_uuid(id), FOREIGN KEY (project_id) REFERENCES projects_uuid(id), FOREIGN KEY (demand_id) REFERENCES demands_uuid(id));

