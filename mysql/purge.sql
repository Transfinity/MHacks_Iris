/* purge.sql
 * tear down the iris mysql database
 *
 * to run:
 *   linux$ mysql -u root -p
 *      Enter password:
 *   mysql> source purge.sql
 *   mysql> quit
 */
DROP DATABASE irisdb;

DROP USER 'iris_ocr'@'localhost';
DROP USER 'iris_webapp'@'localhost';
