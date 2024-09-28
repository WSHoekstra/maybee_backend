<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![LinkedIn][linkedin-shield]][linkedin-url]


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/WSHoekstra/maybee_backend">  
  <img src="images/bee.png" alt="Logo" width="80" height="80" title="Bee icons created by Freepik - Flaticon">
  </a>

  <h3 align="center">Maybee backend</h3>

  <p align="center">
    Restful API for non-contextual multi armed bandits.
    <br />
    ·
    <a href="https://github.com/WSHoekstra/maybee_backend/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    ·
    <a href="https://github.com/WSHoekstra/maybee_backend/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>


<!-- ABOUT THE PROJECT -->
## About The Project
Maybee is a restful API that implements non-contextual multi armed bandits.
Its name is a play on the abbreviation MAB (multi armed bandit).

MABs are a class of algorithms in reinforcement learning that aim to quickly learn how to make good decisions when choosing between many different 'arms' (the equivalent to an 'experimental condition' in A/B/C testing) in order to optimize for some reward function. 

MABs are a particularly attractive alternative to A/B/C testing when perfect certainty about which arm yields the highest avg rewards is less important than quickly making smart decisions, or when it's impractical or even impossible to keep a constant set of arms / experimental conditions.


<!-- PROJECT STATUS -->
### Project Status
This project is in the 0.x stage.
You should expect this project to change rapidly new versions to include breaking changes.


### Built With
* Python
* Poetry
* FastAPI
* SQLModel


<!-- GETTING STARTED -->
## Getting Started

To get started, please explore the Makefile.
Since this project is docker based, you'll need an active Docker machine to execute these commands. 

Build the docker image
```sh
make build
```

Start the application in docker compose with a postgres database
```sh
make up
```


<!-- USAGE EXAMPLES -->
## Usage

This API implements the core concepts of MABs:
- environments (analogous to an experiment)
- arms (analogous to an experimental condition)
- actions (which represent the actions taken by the bandit)
- observations (which represent the observations of a reward, or the lack thereof, as a result of the actions taken)



<!-- ROADMAP -->
## Roadmap

- [x] Create python backend
- [x] Implement epsilon-greedy, softmax, and UCB1 bandits
- [x] Add unit tests
- [x] Create python client library
- [ ] Set up CRUD methods for all available entities.
- [ ] Create React frontend


See the [open issues](https://github.com/WSHoekstra/maybee_backend/issues) for a full list of proposed features (and known issues).


<!-- LICENSE -->
## License
Distributed under the GPL-3.0 license.


<!-- CONTACT -->
## Contact

Walter Hoekstra (https://www.linkedin.com/in/walter-hoekstra-aa26b750/)

Project Link: [https://github.com/WSHoekstra/maybee_backend](https://github.com/WSHoekstra/maybee_backend)


<!-- ACKNOWLEDGMENTS -->
## Acknowledgments
Special thanks to John Myles White (https://github.com/johnmyleswhite), the author of 'Bandit Algorithms for Website Optimization' for inspiring this project.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: www.linkedin.com/in/walter-hoekstra-aa26b750
