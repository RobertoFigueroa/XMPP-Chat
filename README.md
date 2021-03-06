# XMPP-Chat

<br />
<p align="center">
  <a href="https://github.com/RobertoFigueroa/XMPP-Chat#about-the-project">
    <img src="xmpp.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">XMPP Chat Project</h3>

  <p align="center">
    Basic chat functionalities to understand XMPP and how network works!
    <br />
    </p>
</p>

<!-- TABLE OF CONTENTS -->
<details open="open">
 <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#implemented-features">Implemented features</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgements">Acknowledgements</a></li>
  </ol>
</details>

## About The Project

This is a chat build over XMPP, which is a protocol based on XML stanzas. This is part of a project for CC3067 class.

![chat](https://github.com/RobertoFigueroa/XMPP-Chat/blob/main/project.png?raw=true)

## Getting Started

### Prerequisites

You need to have Python 3 with pip in order to run and install the project with all its dependencies.

You also need a XMPP server running like Openfire.

### Installation
1. Clone the repo
2. Install dependencies
* pip packages installation
  ```sh
  pip install -r requirements.txt
  ```
3. Run chat.py file
  ```sh
  python3 chat.py
  ```
4. Use flags for debug and other functionalities
* -d: for debug mode
* -r: for remove account
* -n: create a new account
* no-flags: log in

## Usage

Click in the following link for a demo:

[See the video here 📹](https://youtu.be/PPYTJ7g0ccQ)

## Implemented features

- [x] Sign in with an account

- [x] Register a new account 

- [x] Sign out with an account

- [x] Delete the account

- [x] Show roster

- [x] Show contact details

- [x] Add a user to contacts

- [x] Chat 1 to 1

- [x] Chat room conversations

- [x] Set precence status

- [x] Send and receive files

## Contact

Email: fig18306@uvg.edu.gt

## Acknowledgements

Thanks for Miguel Novella for reply all the questions that I made and for creating a Openfire server to test this project.


