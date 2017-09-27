<?php
/**
 * PostGIS to GeoJSON #source: https://gist.github.com/bmcbride/1913855
 * Query a PostGIS table or view and return the results in GeoJSON format, suitable for use in OpenLayers, Leaflet, etc.
 * 
 * @param 		string		$geotable		The PostGIS layer name *REQUIRED*
 * @param 		string		$geomfield		The PostGIS geometry field *REQUIRED*
 * @param 		string		$srid			The SRID of the returned GeoJSON *OPTIONAL (If omitted, EPSG: 4326 will be used)*
 * @param 		string 		$fields 		Fields to be returned *OPTIONAL (If omitted, all fields will be returned)* NOTE- Uppercase field names should be wrapped in double quotes
 * @param 		string		$parameters		SQL WHERE clause parameters *OPTIONAL*
 * @param 		string		$orderby		SQL ORDER BY constraint *OPTIONAL*
 * @param 		string		$sort			SQL ORDER BY sort order (ASC or DESC) *OPTIONAL*
 * @param 		string		$limit			Limit number of results returned *OPTIONAL*
 * @param 		string		$offset			Offset used in conjunction with limit *OPTIONAL*
 * @return 		string					resulting geojson string
 * $parameters = 'traffic';
 */

#set cron job so that every time it kickstarts the query, it takes 2 hr time slice OR write so that the leaflet map talks to the php
#so that the hours can be put in as an input

$geotable = 'database_name';
$geomfield = 'geom';
$fields = 'category';
$datetimefield = 'created';
// $datetime = '2016-03-10 17:00:00';
// $datetime2 = '2016-03-11 17:00:00';
$hourinterval = '5';
# use 'NOW()' when ready to kickstart app? (sample: SELECT count(*) FROM $geotable WHERE $datetimefield >= (now() - interval '2 hours') )
$srid = '4326';
$sort = 'ASC';

# this hardcodes in traffic as a parameter.. Need to rewrite query $sql so that it can layer on multiple choices 

function escapeJsonString($value) { # list from www.json.org: (\b backspace, \f formfeed)
  $escapers = array("\\", "/", "\"", "\n", "\r", "\t", "\x08", "\x0c");
  $replacements = array("\\\\", "\\/", "\\\"", "\\n", "\\r", "\\t", "\\f", "\\b");
  $result = str_replace($escapers, $replacements, $value);
  return $result;
}
  

# Connect to PostgreSQL database
    
include 'inputpgsql.php';

# Build SQL SELECT statement and return the geometry as a GeoJSON element in EPSG: 4326

$sql = "SELECT *" . ", st_asgeojson(" . pg_escape_string($geomfield) . ",$srid) AS geojson FROM " . pg_escape_string($geotable);
if (strlen(trim($datetime)) > 0) {
    $sql .= " WHERE " .pg_escape_string($datetimefield)." BETWEEN ".pg_escape_literal($datetime). " AND ".pg_escape_literal($datetime2). "AND lat <> 0";
    } 
else 
    $sql .= " WHERE " .pg_escape_string($datetimefield)." >= (now() - interval '".pg_escape_string($hourinterval)." hours') AND lat <> 0"; 
if (strlen(trim($orderby)) > 0) {
    $sql .= " ORDER BY " . pg_escape_string($orderby) . " " . $sort;
    }
if (strlen(trim($limit)) > 0) {
    $sql .= " LIMIT " . pg_escape_string($limit);
}
if (strlen(trim($offset)) > 0) {
    $sql .= " OFFSET " . pg_escape_string($offset);
}

echo $sql;

# Try query or error
$rs = pg_query($connect, $sql);
if (!$rs) {
    echo "An SQL error occured.\n";
    exit;
}
# Build GeoJSON
$output    = '';
$rowOutput = '';
while ($row = pg_fetch_assoc($rs)) {
    $rowOutput = (strlen($rowOutput) > 0 ? ',' : '') . '{"type": "Feature", "geometry": ' . $row['geojson'] . ', "properties": {';
    $props = '';
    $id    = '';
    foreach ($row as $key => $val) {
        if ($key != "geojson") {
            $props .= (strlen($props) > 0 ? ',' : '') . '"' . $key . '":"' . escapeJsonString($val) . '"';
        }
        if ($key == "id") {
            $id .= ',"id":"' . escapeJsonString($val) . '"';
        }
    }
    
    $rowOutput .= $props . '}';
    $rowOutput .= $id;
    $rowOutput .= '}';
    $output .= $rowOutput;
}
$output = '{ "type": "FeatureCollection", "features": [ ' . $output . ' ]}';
$fp=fopen('/home/ma3map_website/js/tweets.geojson','w');
fwrite($fp, $output);
fclose($fp);
echo ' done';

#source of datetimestamp http://stackoverflow.com/questions/1888544/how-to-select-records-from-last-24-hours-using-sql
?> 