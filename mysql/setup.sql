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
CREATE USER 'iris_ocr'@'localhost' IDENTIFIED BY 'blueballoon';
GRANT ALL ON irisdb.* TO 'iris_ocr'@'localhost';

-- This user is the webapp, and can only read.
CREATE USER 'iris_webapp'@'localhost' IDENTIFIED BY 'redeagle';
GRANT SELECT ON irisdb.* TO 'iris_webapp'@'localhost';
