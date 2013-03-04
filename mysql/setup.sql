/* setup.sql
 * set up the iris mysql database
 *
 * to run:
 *   linux$ mysql -u root -p
 *      Enter password:
 *   mysql> source setup.sql
 *   mysql> quit
 */
-- Construct the database
CREATE DATABASE irisdb;

-- This user will be run from the python, with write privelages
CREATE USER 'iris_ocr'@'domU-12-31-39-14-72-A7.compute-1.internal' IDENTIFIED BY 'blueballoon';
GRANT ALL ON irisdb.* TO 'iris_ocr'@'domU-12-31-39-14-72-A7.compute-1.internal';

-- This user is the webapp, and can only read.
CREATE USER 'iris_webapp'@'domU-12-31-39-14-72-A7.compute-1.internal' IDENTIFIED BY 'redeagle';
GRANT SELECT ON irisdb.* TO 'iris_webapp'@'domU-12-31-39-14-72-A7.compute-1.internal';
