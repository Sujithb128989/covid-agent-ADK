import time
import os

def play_animation():
    """
    Plays a simple boot-up animation.
    """
    frames = [
        """
        [        ]
        """,
        """
        [=       ]
        """,
        """
        [==      ]
        """,
        """
        [===     ]
        """,
        """
        [====    ]
        """,
        """
        [=====   ]
        """,
        """
        [======  ]
        """,
        """
        [======= ]
        """,
        """
        [========]
        """,
        """
        BOOTING UP...
        """,
        """
        COVID-19 DATA AGENT
        """
    ]

    for frame in frames:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(frame)
        time.sleep(0.2)
