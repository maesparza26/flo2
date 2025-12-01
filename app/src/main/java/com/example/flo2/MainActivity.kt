package com.example.flo2

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.foundation.Image
import androidx.compose.ui.res.painterResource
import androidx.compose.material3.Button
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.flo2.ui.theme.Flo2Theme
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.net.HttpURLConnection
import java.net.URL
import org.json.JSONObject
import org.json.JSONArray
import com.patrykandpatryk.vico.compose.chart.Chart
import com.patrykandpatryk.vico.compose.chart.line.lineChart
import com.patrykandpatryk.vico.compose.axis.horizontal.bottomAxis
import com.patrykandpatryk.vico.compose.axis.vertical.startAxis
import com.patrykandpatryk.vico.core.entry.ChartEntry
import com.patrykandpatryk.vico.core.entry.ChartEntryModelProducer
import com.patrykandpatryk.vico.core.entry.entryOf

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            Flo2Theme {
                Scaffold(
                    modifier = Modifier.fillMaxSize()
                ) { innerPadding ->
                    TemperatureFromServerScreen(
                        modifier = Modifier.padding(innerPadding)
                    )
                }
            }
        }
    }
}

@Composable
fun TemperatureFromServerScreen(modifier: Modifier = Modifier) {

    var status by remember { mutableStateOf("Press Refresh for New Temperature") }
    var temp by remember { mutableStateOf("--") }
    var temphistory by remember { mutableStateOf<List<Float>>(emptyList()) }

    val scope = rememberCoroutineScope()

    val chartModelProducer = remember {
        ChartEntryModelProducer(emptyList<ChartEntry>())
    }

    // -------- GET CURRENT TEMPERATURE ----------
    fun retrieveTemperature() {
        scope.launch(Dispatchers.IO) {
            try {
                val url = URL("http://10.0.2.2:8000/temp")
                val conn = (url.openConnection() as HttpURLConnection).apply {
                    requestMethod = "GET"
                    connectTimeout = 3000
                    readTimeout = 3000
                }

                val code = conn.responseCode
                if (code == 200) {
                    val response = conn.inputStream.bufferedReader().use { it.readText() }
                    val json = JSONObject(response)
                    val t = json.optString("temp", "--")

                    temp = t
                    status = "Temperature updated"
                } else {
                    status = "HTTP error $code"
                }

                conn.disconnect()

            } catch (e: Exception) {
                status = "Error: ${e.message}"
            }
        }
    }

    // -------- GET HISTORY FROM PYTHON SERVER ----------
    fun retrieveHistory() {
        scope.launch(Dispatchers.IO) {
            try {
                val url = URL("http://10.0.2.2:8000/history")
                val conn = (url.openConnection() as HttpURLConnection).apply {
                    requestMethod = "GET"
                    connectTimeout = 3000
                    readTimeout = 3000
                }

                val code = conn.responseCode
                if (code == 200) {
                    val response = conn.inputStream.bufferedReader().use { it.readText() }
                    val arr = JSONArray(response)

                    val temps = mutableListOf<Float>()

                    for (i in 0 until arr.length()) {
                        val obj = arr.getJSONObject(i)
                        val tempVal = obj.optDouble("temp", Double.NaN)
                        if (!tempVal.isNaN()) temps.add(tempVal.toFloat())
                    }

                    temphistory = temps

                    val entries = temps.mapIndexed { index, value ->
                        entryOf(index.toFloat(), value)
                    }

                    chartModelProducer.setEntries(entries)

                    status = "History loaded"
                } else {
                    status = "HTTP error $code (history)"
                }

                conn.disconnect()

            } catch (e: Exception) {
                status = "Error (history): ${e.message}"
            }
        }
    }

    // ----------- UI -----------
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {

        // Logo
        Image(
            painter = painterResource(id = R.drawable.logo),
            contentDescription = "FLO2 Logo",
            modifier = Modifier.size(120.dp)
        )

        Text("Temperature Monitor", style = MaterialTheme.typography.headlineSmall)
        Text("Status: $status")

        // -------- Refresh Button --------
        Button(
            onClick = {
                retrieveTemperature()
                retrieveHistory()
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Refresh")
        }

        // -------- Current Temperature Card --------
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text("Current Temperature")
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "$temp °C",
                    fontSize = 40.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }

        // -------- History Chart --------
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .height(260.dp),
            shape = RoundedCornerShape(16.dp)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(16.dp)
            ) {
                Text("Temperature History")
                Spacer(modifier = Modifier.height(12.dp))

                if (temphistory.isNotEmpty()) {
                    Chart(
                        chart = lineChart(),
                        chartModelProducer = chartModelProducer,
                        startAxis = startAxis(),
                        bottomAxis = bottomAxis()
                    )
                } else {
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        Text("No history loaded yet")
                    }
                }
            }
        }
    }
}
