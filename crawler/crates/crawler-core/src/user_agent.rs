// crawler/crates/crawler-core/src/user_agent.rs
use rand::seq::SliceRandom;
use rand::thread_rng;

pub struct UserAgentRotator {
    agents: Vec<String>,
}

impl UserAgentRotator {
    pub fn new(agents: Vec<String>) -> Self {
        assert!(!agents.is_empty(), "At least one user-agent required");
        Self { agents }
    }

    pub fn get(&self) -> &str {
        let mut rng = thread_rng();
        self.agents.choose(&mut rng).unwrap()
    }
}
