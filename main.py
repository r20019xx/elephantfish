import sys, time, re
from tools import mrender
from algorithms.elephantfish import Searcher, Position, initial


def write(message, log_file='debug.log'):
    """
    Write a message to the specified log file.
    """
    # try:
    #     # print(f"Writing message: {message} to log file: {log_file}")
    #     with open(log_file, mode='a', encoding='utf-8') as log:
    #         log.write(f"{message}\n")
    # except IOError as error:
    #     print(f"Failed to write to {log_file}: {error}")
    #     raise


def parse_position(command, hist):
    """
    Parse the position command and synchronize the history.
    """
    tokens = command.strip().split()
    if len(tokens) < 2:
        print("info string Invalid position command")
        sys.stdout.flush()
        return
    if tokens[1] == 'startpos':
        # Reset history to the initial position
        hist.clear()
        hist.append(Position(initial, 0))
    elif tokens[1] == 'fen':
        # Parse moves
        moves = tokens[tokens.index('moves') + 1:] if 'moves' in tokens else []
        # Synchronize hist with the new position and moves
        if len(moves) < len(hist) - 1:
            # If the new moves are fewer, truncate hist
            hist = hist[:len(moves) + 1]
        elif len(moves) > len(hist) - 1:
            # If the new moves are more, append missing moves to hist
            for index, move_str in enumerate(moves[len(hist) - 1:]):
                # We query the user until she enters a (pseudo) legal move.
                match = re.match('([a-i][0-9])' * 2, move_str)
                if match:
                    move = parse(match.group(1)), parse(match.group(2))
                    if index % 2 == 1:
                        move = (parse(render(255 - move[0] - 1)), parse(render(255 - move[1] - 1)))
                    hist.append(hist[-1].move(move))
            sys.stdout.flush()
        print(hist[-1][0])

    else:
        print("info string Unknown position type")
        sys.stdout.flush()
        return

    print(f"info string Synchronized history length: {len(hist)}")
    sys.stdout.flush()


A0, I0, A9, I9 = 12 * 16 + 3, 12 * 16 + 11, 3 * 16 + 3, 3 * 16 + 11


def parse(c):
    fil, rank = ord(c[0]) - ord('a'), int(c[1])
    return A0 + fil - 16 * rank


def render(i):
    rank, fil = divmod(i - A0, 16)
    return chr(fil + ord('a')) + str(-rank)


def handle_go_command(command, hist, searcher):
    think_time = 5
    tokens = command.split()
    if 'movetime' in tokens:
        think_time = int(tokens[tokens.index('movetime') + 1]) / 1000
    start = time.time()
    this_move, best_move, max_score = None, None, None

    # If is_black_turn is True, the engine is playing black (rotate board).
    is_black_turn = len(hist) % 2 == 0
    search_position = hist[-1].rotate() if is_black_turn else hist[-1]
    write('BLACK Turn' if is_black_turn else 'RED Turn')

    # Search for the best move
    for depth, move, score in searcher.search(hist[-1], hist):
        elapsed_time = int((time.time() - start) * 1000)

        this_move = (
            # If is_black_turn is True, we need to rotate the move back.
            mrender(hist[-1], (parse(render(255 - move[0] - 1)), parse(render(255 - move[1] - 1))))
            if is_black_turn
            else mrender(hist[-1], move)
        )

        write(f"info depth {depth} score cp {score} time {elapsed_time} nps {searcher.nodes} pv {this_move}")
        print(f"info depth {depth} score cp {score} time {elapsed_time} nps {searcher.nodes} pv {this_move}")
        sys.stdout.flush()

        if max_score is None or score >= max_score:
            max_score = score
            best_move = this_move

        if time.time() - start > think_time:
            write('timeout')
            break

    if best_move:
        print(f"bestmove {best_move}")
        write(f"bestmove {best_move}")
    else:
        print("bestmove 0000")

    hist.append(hist[-1].move(move))
    write(f'{hist[-1][0]}')

    sys.stdout.flush()


def uci_loop():
    hist = [Position(initial, 0)]
    searcher = Searcher()
    while True:
        command = sys.stdin.readline().strip()
        write('Command: ' + command)
        if command == 'uci':
            print("id name SimpleChineseChessEngine")
            print("id author YourName")
            print("uciok")
            sys.stdout.flush()
        elif command == 'isready':
            print("readyok")
            sys.stdout.flush()
        elif command == 'ucinewgame' or command == 'stop':
            hist = [Position(initial, 0)]
            searcher = Searcher()
        elif command.startswith('position'):
            parse_position(command, hist)
        elif command.startswith('go'):
            handle_go_command(command, hist, searcher)
        elif command == 'quit':
            break
        else:
            write(f"info string Unknown command: {command}")
            print(f"info string Unknown command: {command}")
            sys.stdout.flush()


if __name__ == "__main__":
    uci_loop()
