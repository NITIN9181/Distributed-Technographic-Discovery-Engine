//! Basic async HTTP fetcher - proof of concept for Phase 4
//! 
//! Usage:
//!   rust_crawler <url>
//!   rust_crawler --batch urls.txt
//! 
//! Output: JSON with url, status, headers, body_length, body (first 10KB)

use clap::Parser;
use reqwest::Client;
use serde::Serialize;
use std::time::Duration;
use std::fs::File;
use std::io::{self, BufRead};
use std::path::Path;

#[derive(Parser)]
#[command(name = "rust_crawler")]
struct Args {
    /// URL to fetch
    url: Option<String>,
    
    /// File with URLs (one per line)
    #[arg(long)]
    batch: Option<String>,
}

#[derive(Serialize)]
struct FetchResult {
    url: String,
    final_url: String,
    status: u16,
    headers: std::collections::HashMap<String, String>,
    body_length: usize,
    body_preview: String,  // First 10KB
    error: Option<String>,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();
    
    let client = Client::builder()
        .timeout(Duration::from_secs(15))
        .user_agent("TechDetector-RustCrawler/0.1")
        .redirect(reqwest::redirect::Policy::limited(5))
        .build()?;
    
    if let Some(url) = args.url {
        let result = fetch_url(&client, &url).await;
        let json = serde_json::to_string_pretty(&result)?;
        println!("{}", json);
    } else if let Some(batch_file) = args.batch {
        if let Ok(lines) = read_lines(batch_file) {
            let mut results = Vec::new();
            for line in lines {
                if let Ok(domain) = line {
                    if domain.trim().is_empty() {
                        continue;
                    }
                    let url = if domain.starts_with("http") {
                        domain
                    } else {
                        format!("https://{}", domain)
                    };
                    
                    let result = fetch_url(&client, &url).await;
                    results.push(result);
                }
            }
            let json = serde_json::to_string_pretty(&results)?;
            println!("{}", json);
        }
    } else {
        println!("Please provide a URL or --batch file. Run with --help for usage.");
    }
    
    Ok(())
}

fn read_lines<P>(filename: P) -> io::Result<io::Lines<io::BufReader<File>>>
where P: AsRef<Path>, {
    let file = File::open(filename)?;
    Ok(io::BufReader::new(file).lines())
}

async fn fetch_url(client: &Client, url: &str) -> FetchResult {
    let target_url = if url.starts_with("http") {
        url.to_string()
    } else {
        format!("https://{}", url)
    };

    match client.get(&target_url).send().await {
        Ok(response) => {
            let final_url = response.url().to_string();
            let status = response.status().as_u16();
            
            let mut headers = std::collections::HashMap::new();
            for (key, value) in response.headers().iter() {
                if let Ok(val_str) = value.to_str() {
                    headers.insert(key.as_str().to_string(), val_str.to_string());
                }
            }
            
            match response.text().await {
                Ok(body) => {
                    let body_length = body.len();
                    // Preview up to 10KB
                    let body_preview = if body_length > 10240 {
                        body[..10240].to_string()
                    } else {
                        body
                    };
                    
                    FetchResult {
                        url: target_url,
                        final_url,
                        status,
                        headers,
                        body_length,
                        body_preview,
                        error: None,
                    }
                },
                Err(e) => FetchResult {
                    url: target_url.clone(),
                    final_url,
                    status,
                    headers,
                    body_length: 0,
                    body_preview: String::new(),
                    error: Some(format!("Failed to read body: {}", e)),
                }
            }
        },
        Err(e) => FetchResult {
            url: target_url,
            final_url: String::new(),
            status: 0,
            headers: std::collections::HashMap::new(),
            body_length: 0,
            body_preview: String::new(),
            error: Some(e.to_string()),
        }
    }
}
