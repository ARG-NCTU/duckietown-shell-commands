from dt_shell import DTCommandAbs, DTShell


class DTCommand(DTCommandAbs):
    help = 'Duckiepond command'

    @staticmethod
    def command(shell: DTShell, args):

        print("Hello my Duckiebot!")
        print(
            'You called the "%s" command, level %d, with arguments %r' % (
                DTCommand.name,
                DTCommand.level,
                args
            )
        )

        exit()

    @staticmethod
    def complete(shell, word, line):
        # this function will be invoked when the user presses the [Tab] key for auto completion.
        #
        #   shell   is the instance of DTShell hosting this command
        #   word    is the right-most word typed in the terminal
        #           (usually the string the user is trying to auto-complete)
        #
        #   return  a list of strings. Each string is a suggestion for the user
        #
        # PUT YOUR CODE HERE
        return ['suggestion_1', 'suggestion_2']
