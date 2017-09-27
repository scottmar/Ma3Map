<?php
$connect = pg_connect("host=localhost port=FILL IN YOUR OWN dbname=FILL IN YOUR OWN user=FILL IN YOUR OWN password=FILL IN YOUR OWN");
if (!$connect) {
    die("Connection failed");
}
else {
    echo "yay!";
}
?>